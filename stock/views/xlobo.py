import asyncio
import base64
import logging
import os.path
from collections import OrderedDict
from io import BytesIO

import aiohttp
import arrow
from PyPDF2 import PdfFileMerger, PdfFileReader
from django.conf import settings
from django.db import IntegrityError, connection, transaction
from django.db.models import F
from rest_framework import status, views
from rest_framework.exceptions import APIException
from rest_framework.response import Response

from stock.models import (Inventory, Order, Product, PurchaseOrderItem,
                          Shipping, ShippingDB, Stock, TransformDB)
from ymatou import japanems, utils, ymatouapi

YMTKEY = {
    '东京彩虹桥': {
        'appid': 'llzlHWWDTkEsUUjwKf',
        'appsecret': 'xdP5yraJQdpypKZNQ0M0zqE35dcrEWox',
        'authcode': 'Ul1BpFlBHdLR6EnEv75RV6QeradgjdBk'
    },
    '妈妈宝宝日本馆': {
        'appid': 'B9EBxjEN4JYB58BG4B',
        'appsecret': 'AKiwySBsiIwqz2TkkgQPXOJgCooc97Jt',
        'authcode': '6SJRmS03o6kwoYjqNPjUXocfMK0MpLhT'
    }
}

access_token = 'AESaZpmFNNcLRbNFmWK38S2ELvpzwjHkRjkpJkNmaaRIpEJ7T+FYBfVvoekui/2k1g=='
client_secret = 'APvYM8Mt5Xg1QYvker67VplTPQRx28Qt/XPdY9D7TUhaO3vgFWQ71CRZ/sLZYrn97w=='.lower(
)
client_id = '8417db83-360c-4275-974f-cf9a2734d8f8'

# debug
# access_token = 'ACiYUZ6aKC48faYFD6MpvbOf73BdE9OV5g15q1A6Ghs+i/XIawq/9RHJCzc6Y3UNxA=='
# client_secret = 'APvYM8Mt5Xg1QYvker67VplTPQRx28Qt/XPdY9D7TUhaO3vgFWQ71CRZ/sLZYrn97w=='.lower(
# )
# client_id = '68993573-E38D-4A8A-A263-055C401F9369'

logger = logging.getLogger(__name__)


# ymatou order need check orderstatus
# 这里可能有合并订单发货情况, 需要根据订单ID去重, 然后去码头后台查每一
# 个订单状态是否正常
def checkOrderStatus(loop, sess, ords, disable_checkOrderDelivery=False):
    ordObj = Order.objects.get(id=ords[0]['id'])
    errmsg = None
    if ordObj.shippingdb:
        raise APIException({'errmsg': '订单已出面单, 请及时刷新页面'})
    if '洋码头' in ords[0]['channel_name']:
        skey = YMTKEY[ords[0]['seller_name']]
        ymtapi = ymatouapi.YmatouAPI(sess, skey['appid'], skey['appsecret'],
                                     skey['authcode'])
        ordids = list([OrderedDict.fromkeys([i['orderid'] for i in ords])])
        for oid in ordids:
            result = loop.run_until_complete(
                ymtapi.getOrderInfo(ords[0]['orderid']))
            # result = loop.run_until_complete(ymtapi.getOrderInfo('127086025'))
            if result['content']['order_info']['order_status'] in [12, 13, 14]:
                errmsg = '订单已关闭, 请到码头后台确认'
            if not disable_checkOrderDelivery:
                if result['content']['order_info']['order_status'] in [3, 4]:
                    errmsg = '订单已发货, 请到码头后台确认'
            for oi in result['content']['order_info']['order_items_info']:
                if oi['refund_status'] == 0:
                    errmsg = '订单退款审核中, 请到码头后台确认'
                    break
            if errmsg:
                raise APIException({'errmsg': errmsg})
        return None


def deliveryYMTOrder(loop, sess, ord, db_number):
    skey = YMTKEY[ord['seller_name']]
    ymtapi = ymatouapi.YmatouAPI(sess, skey['appid'], skey['appsecret'],
                                 skey['authcode'])
    shipObj = Shipping.objects.get(id=ord['shipping'])
    r = loop.run_until_complete(
        ymtapi.deliver(ord['orderid'], db_number, shipObj.delivery_company))
    if '0000' in r.get('code') and r.get('content'):
        info = r['content']['results']
        if not info or info[0]['exec_success']:
            return '已发货'
        else:
            raise APIException({'errmsg': info[0]['msg']})


def checkUserOtherOrder(ords):
    # 如果need_check, 需要先查一下该用户是否有其他订单没有一并提交, 如果有, 返回
    # 异常
    check_ords = Order.objects.filter(
        receiver_name=ords[0]['receiver_name'],
        receiver_mobile=ords[0]['receiver_mobile'],
        shippingdb__isnull=True,
        status__in=['待处理', '待采购', '需面单', '已采购', '需介入'])
    if len(check_ords) != len(ords):
        raise APIException({'errmsg': '该用户有其他订单, 请检查.'})
    return None


def checkInputOrder(ords):
    t = set([(o['inventory'], o['shipping'], o['receiver_name'],
              o['receiver_address'], o['receiver_mobile']) for o in ords])
    if len(t) > 1:
        raise APIException({'errmsg': '订单信息不一致, 请检查.'})
    return None


def getXloboAPI(sess):
    return ymatouapi.XloboAPI(sess, access_token, client_secret, client_id)


def getJapanEMSStorageLocal():
    return settings.EMS_STORAGE_DIR


# 1. 生成DB面单, 如果是码头订单, 需要先确认订单状态, 状态异常, 直接返回异常
# 2. 需要考虑该用户是否有其他订单, 如果有其他订单, 需要提醒操作人员.
class XloboCreateNoVerification(views.APIView):
    def post(self, request, format=None):
        data = request.data
        ords = data['orders']
        disable_check = data['disable_check']
        totalAmount = sum(
            [float(i['price']) * float(i['quantity']) for i in ords])
        if totalAmount > 2000:
            raise APIException({'errmsg': '订单金额超2000不能发贝海.'})

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop = asyncio.get_event_loop()
        sess = aiohttp.ClientSession(
            loop=loop, connector=aiohttp.TCPConnector(verify_ssl=False))

        checkInputOrder(ords)
        checkOrderStatus(loop, sess, ords)
        if not disable_check:
            checkUserOtherOrder(ords)

        # create db number
        # construct api msg
        channel_name = ords[0]['channel_name']
        address = ords[0]['receiver_address'].split(',')
        order_piad_time = ords[0]['piad_time']
        billSenderInfo = {
            'Name': ords[0]['seller_name'],
            'Address': '埼玉県朝霞市泉水３-7-9-115',
            'Phone': '08030097238',
        }
        if data['set_sender']:
            billSenderInfo['Name'] = data['sender_name']
            billSenderInfo['Phone'] = data['sender_mobile']

        billReceiverInfo = {
            'Name': ords[0]['receiver_name'],
            'Province': address[0],
            'City': address[1],
            'District': address[2],
            'Address': address[3],
            'Phone': ords[0]['receiver_mobile'],
            'PostCode': ords[0]['receiver_zip'],
            'IdCode': ords[0].get('receiver_idcard')
        }
        billSupplyInfo = {
            'OrderCode': ','.join(set([o['orderid'] for o in ords])),
            'TradingNo': '11111111',
            'ChannelName': channel_name
        }
        billCategoryList = []
        for o in ords:
            productObj = Product.objects.get(jancode=o['jancode'])
            bcl = {
                'CategoryId': productObj.category.id,
                'CategoryVersion': productObj.category.category_version,
                'Count': o['quantity'],
                'UnitPrice': o['price'],
                'ProductName': productObj.name,
                'Brand': productObj.brand,
                'Specification': productObj.specification
            }
            billCategoryList.append(bcl)

        data.pop('orders')
        data['BillSenderInfo'] = billSenderInfo
        data['BillReceiverInfo'] = billReceiverInfo
        data['BillSupplyInfo'] = billSupplyInfo
        data['BillCategoryList'] = billCategoryList

        xloboapi = getXloboAPI(sess)
        result = loop.run_until_complete(xloboapi.createNoVerification(data))
        logger.debug('XloboCreateNoVerification: %s', result)
        if result['ErrorCount'] > 0:
            raise APIException({
                'errmsg':
                result['ErrorInfoList'][0]['ErrorDescription'],
            })
        loop.close()
        # if result['ErrorCount']:
        #     return Response(data=result, status=status.HTTP_400_BAD_REQUEST)

        # save shippingdb & update order(shippingdb)
        with transaction.atomic():
            shippingObj = Shipping.objects.get(id=ords[0]['shipping'])
            inventoryObj = Inventory.objects.get(id=ords[0]['inventory'])
            shippingdbObj = ShippingDB(
                db_number=result['Result']['BillCode'],
                status='待处理',
                pre_sale=ords[0]['pre_sale'],
                order_piad_time=order_piad_time,
                channel_name=channel_name,
                shipping=shippingObj,
                inventory=inventoryObj)
            shippingdbObj.save()
            for o in ords:
                orderObj = Order.objects.get(id=o['id'])
                orderObj.shippingdb = shippingdbObj
                if orderObj.status == '需面单':
                    orderObj.status = '待发货'
                orderObj.save(update_fields=['shippingdb', 'status'])

        return Response(data=result, status=status.HTTP_200_OK)


# 虚仓电商无需我们自己再处理, 直接贝海负责打包发货
class XloboCreateFBXBill(views.APIView):
    def post(self, request, format=None):
        data = request.data
        ords = data['orders']
        disable_check = data['disable_check']
        channinfo = {
            '洋码头': 2,
            '天猫': 3,
            '苏宁': 4,
            '京东': 5,
            '淘宝': 6,
            '一号店': 8,
            '当当': 9,
            'Higo': 10,
            '其他渠道': 7
        }
        totalAmount = sum(
            [float(i['price']) * float(i['quantity']) for i in ords])
        if totalAmount > 2000:
            raise APIException({'errmsg': '订单金额超2000不能发贝海.'})

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop = asyncio.get_event_loop()
        sess = aiohttp.ClientSession(
            loop=loop, connector=aiohttp.TCPConnector(verify_ssl=False))

        checkInputOrder(ords)
        checkOrderStatus(loop, sess, ords)
        if not disable_check:
            checkUserOtherOrder(ords)

        # construct api msg
        channel_name = ords[0]['channel_name']
        address = ords[0]['receiver_address'].split(',')
        order_piad_time = ords[0]['piad_time']
        billSenderInfo = {
            'Name': ords[0]['seller_name'],
            'Address': '埼玉県朝霞市泉水3-7-9-115',
            'Phone': '08030097238',
        }
        if data['set_sender']:
            billSenderInfo['Name'] = data['sender_name']
            billSenderInfo['Phone'] = data['sender_mobile']

        billReceiverInfo = {
            'Name': ords[0]['receiver_name'],
            'Province': address[0],
            'City': address[1],
            'District': address[2],
            'Address': address[3],
            'Phone': ords[0]['receiver_mobile'],
            'PostCode': ords[0]['receiver_zip'],
            'IdCode': ords[0].get('receiver_idcard')
        }
        billSupplyInfo = {
            'OrderCode': ords[0]['orderid'],
            'BillThirdPartType': channinfo[channel_name],
            'ChannelName': channel_name
        }
        billCategoryList = []
        for o in ords:
            bcl = {
                'ProductNo': o['jancode'],
                'Count': o['quantity'],
                'Price': o['price'],
            }
            billCategoryList.append(bcl)

        data.pop('orders')
        data['IsReceiveTax'] = data['IsRecTax']
        data['PackingType'] = data['IsRePacking']
        data['BillSenderInfo'] = billSenderInfo
        data['BillReceiverInfo'] = billReceiverInfo
        data['BillSupplyInfo'] = billSupplyInfo
        data['GoodsSkuInfos'] = billCategoryList

        xloboapi = getXloboAPI(sess)
        result = loop.run_until_complete(xloboapi.createFBXBill(data))
        logger.debug('XloboCreateFBXBill: %s', result)
        if result['ErrorCount'] > 0:
            raise APIException({
                'errmsg':
                result['ErrorInfoList'][0]['ErrorDescription'],
            })
        loop.close()
        # if result['ErrorCount']:
        #     return Response(data=result, status=status.HTTP_400_BAD_REQUEST)

        # save shippingdb & update order(shippingdb)
        with transaction.atomic():
            shippingObj = Shipping.objects.get(id=ords[0]['shipping'])
            inventoryObj = Inventory.objects.get(id=ords[0]['inventory'])
            shippingdbObj = ShippingDB(
                db_number=result['Result']['BillCode'],
                status='已出库',
                pre_sale=ords[0]['pre_sale'],
                order_piad_time=order_piad_time,
                channel_name=channel_name,
                shipping=shippingObj,
                inventory=inventoryObj)
            shippingdbObj.save()
            for o in ords:
                orderObj = Order.objects.get(id=o['id'])
                orderObj.shippingdb = shippingdbObj
                orderObj.status = '已发货'  # 订单直接进入已发货状态
                orderObj.save(update_fields=['status', 'shippingdb'])
                stockObj = Stock.objects.get(
                    product__jancode=orderObj.jancode,
                    inventory=orderObj.inventory)
                stockObj.quantity = F('quantity') - orderObj.quantity  # 扣减库存
                stockObj.preallocation = F('preallocation') - orderObj.quantity
                stockObj.save()

        return Response(data=result, status=status.HTTP_200_OK)


class CreateJapanEMS(views.APIView):
    def post(self, request, format=None):
        data = request.data
        ords = data['orders']
        disable_check = data['disable_check']
        country = data['country']
        tax_included_channel = data['tax_included_channel']

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop = asyncio.get_event_loop()
        sess = aiohttp.ClientSession(loop=loop)

        checkInputOrder(ords)
        checkOrderStatus(loop, sess, ords)
        if not disable_check:
            checkUserOtherOrder(ords)

        # create ems number
        # sendType
        #    EMS(物品): 1 / 国际e包裹: 4 / 国际邮包: 5
        # transType
        #    航空: 1 / 标准航空(SAL): 3 / 海运: 2
        shippingInfo = {
            'EMS': (1, None),
            'EPACK': (4, None),
            'SAL': (5, 3),
            'SURFACE': (5, 2)
        }
        sendType = shippingInfo[ords[0]['shipping_name']][0]
        transType = shippingInfo[ords[0]['shipping_name']][1]
        ems_number = japanems.createJapanEMS(
            ords[0], sendType, transType, country=country)

        with transaction.atomic():
            shippingObj = Shipping.objects.get(id=ords[0]['shipping'])
            inventoryObj = Inventory.objects.get(id=ords[0]['inventory'])
            taxIncluded = '是' if tax_included_channel else None
            shippingdbObj = ShippingDB(
                db_number=ems_number,
                status='待处理',
                order_piad_time=ords[0]['piad_time'],
                channel_name=ords[0]['channel_name'],
                tax_included_channel=taxIncluded,
                shipping=shippingObj,
                pre_sale=ords[0]['pre_sale'],
                inventory=inventoryObj)
            shippingdbObj.save()
            for o in ords:
                orderObj = Order.objects.get(id=o['id'])
                orderObj.shippingdb = shippingdbObj
                if orderObj.status == '需面单':
                    orderObj.status = '待发货'
                orderObj.save(update_fields=['shippingdb', 'status'])

        return Response(status=status.HTTP_200_OK)


class CreateTransformDB(views.APIView):
    def post(self, request, format=None):
        # create ems number
        # sendType
        #    EMS(物品): 1 / 国际e包裹: 4 / 国际邮包: 5
        # transType
        #    航空: 1 / 标准航空(SAL): 3 / 海运: 2
        shippingInfo = {
            'EMS': (1, None),
            'EPACK': (4, None),
            'SAL': (5, 3),
            'SURFACE': (5, 2)
        }
        data = request.data
        pois = data['pois']
        si = data.get('ems_type', None)
        db_number = data.get('db_number', None)
        if not db_number:
            sendType = shippingInfo[si][0]
            transType = shippingInfo[si][1]
            ord = {
                'receiver_name': data['receiver_name'],
                'receiver_address': data['receiver_address'],
                'receiver_zip': data['receiver_zip'],
                'receiver_mobile': data['receiver_mobile'],
                'jancode': pois[0]['jancode'],
                'orderid': pois[0]['orderid'],
            }
            db_number = japanems.createJapanEMS(ord, sendType, transType)

        with transaction.atomic():
            inventoryObj = Inventory.objects.get(id=4)
            try:
                transformdbObj = TransformDB.objects.get(db_number=db_number)
                if transformdbObj.status == '已出库':
                    raise IntegrityError
            except TransformDB.DoesNotExist:
                transformdbObj = TransformDB(
                    db_number=db_number,
                    status='待处理',
                    inventory=inventoryObj,
                    create_time=arrow.now().format('YYYY-MM-DD HH:mm:ss'))
                transformdbObj.save()
            for o in pois:
                poiObj = PurchaseOrderItem.objects.get(id=o['id'])
                poiObj.transformdb = transformdbObj
                poiObj.status = '转运中'
                poiObj.delivery_no = db_number
                poiObj.save(
                    update_fields=['transformdb', 'status', 'delivery_no'])

        return Response(status=status.HTTP_200_OK)


# 思考: 拼邮订单, 还是需要填写正确的EMS单号, 否则不容易追踪包裹情况, 但是存在
# 不正确填写EMS单号的情况, 这个需要怎么处理?
class ManualAllocateDBNumber(views.APIView):
    def post(self, request, format=None):
        ords = request.data['orders']
        disable_check = request.data['disable_check']
        disable_checkOrderDelivery = request.data[
            'disable_checkOrderDelivery']  # 走贝海系统生成的面单, 会直接码头后台发货, 这样的DB面单回填到系统的时候, 不能检查订单状态, 否则报错
        disable_channel_delivery = request.data['disable_channel_delivery']
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop = asyncio.get_event_loop()
        sess = aiohttp.ClientSession(
            loop=loop, connector=aiohttp.TCPConnector(verify_ssl=False))

        checkInputOrder(ords)
        checkOrderStatus(loop, sess, ords, disable_checkOrderDelivery)
        if not disable_check:
            checkUserOtherOrder(ords)

        db_number = request.data['Comment']
        if not db_number:
            raise APIException({'errmsg': '面单号不能为空.'})
        channel_name = ords[0]['channel_name']
        order_piad_time = ords[0]['piad_time']
        # delivery_type = ords[0]['delivery_type']

        # 如果洋码头订单, 先用回填面单发货
        delivery_status = None
        if disable_channel_delivery:
            delivery_status = '已发货'
        elif ords[0]['channel_name'] == '洋码头':
            delivery_status = deliveryYMTOrder(loop, sess, ords[0], db_number)

        with transaction.atomic():
            orderStatus = None
            shippingdbObj = None
            try:
                shippingdbObj = ShippingDB.objects.get(db_number=db_number)
                for o in ords:
                    if '拼邮' not in o['shipping_name']:
                        raise APIException({
                            'errmsg':
                            '非拼邮订单, 面单号被重复使用, 请仔细检查确认',
                        })
                    elif '拼邮' in o['shipping_name'] and '洋码头' in o['channel_name'] and '拼邮' not in o['delivery_type']:
                        if shippingdbObj.channel_name == '京东' and shippingdbObj.status == '已出库':
                            pass
                        else:
                            raise APIException({
                                'errmsg':
                                '该订单为直邮转拼邮发货, 需使用直邮面单号发货',
                            })
                    else:
                        if shippingdbObj.status != '已出库':
                            raise APIException({
                                'errmsg':
                                '使用了直邮面单, 但面单尚未出库, 请仔细检查确认',
                            })
                        c = shippingdbObj.order.count()
                        if c > 500:
                            raise APIException({
                                'errmsg':
                                '该国际单号被重复使用次数过多, 请换新单号发货',
                            })
            except ShippingDB.DoesNotExist:
                shippingObj = Shipping.objects.get(id=ords[0]['shipping'])
                inventoryObj = Inventory.objects.get(id=ords[0]['inventory'])
                dbStatus = '待处理'
                if '贝海' in inventoryObj.name and 'EMS' in shippingObj.name:  # 贝海EMS无需我们打包
                    dbStatus = '已出库'
                    orderStatus = '已发货'  # TODO: 采购可能没有到库
                if shippingObj.name in ['拼邮', '轨迹']:  # 拼邮不进入待发货列表, 但是需打包发货
                    dbStatus = '已出库'
                shippingdbObj = ShippingDB(
                    db_number=db_number,
                    # status='已出库' if '拼邮' in delivery_type else '待处理',   # 如果是拼邮订单, 只是需要一个面单回填, 无需做国外发货处理
                    status=dbStatus,
                    channel_name=channel_name,
                    order_piad_time=order_piad_time,
                    shipping=shippingObj,
                    inventory=inventoryObj)
                shippingdbObj.save()

            for o in ords:
                orderObj = Order.objects.get(id=o['id'])
                orderObj.shippingdb = shippingdbObj
                if orderStatus:
                    orderObj.status = orderStatus
                    stockObj = Stock.objects.get(
                        product__jancode=orderObj.jancode,
                        inventory=orderObj.inventory)
                    stockObj.quantity = F(
                        'quantity') - orderObj.quantity  # 扣减库存
                    stockObj.preallocation = F(
                        'preallocation') - orderObj.quantity
                    stockObj.save()
                # if disable_channel_delivery:
                #     orderObj.channel_delivery_status = '已发货'
                if delivery_status:
                    orderObj.channel_delivery_status = delivery_status
                if orderObj.status == '需面单':
                    orderObj.status = '待发货'
                orderObj.save(update_fields=[
                    'shippingdb', 'status', 'channel_delivery_status'
                ])

        return Response(status=status.HTTP_200_OK)


# 删除DB面单, 清理订单的shippingdb_id字段
class XloboDeleteDBNumber(views.APIView):
    def post(self, request, format=None):
        # construct api msg
        data = request.data
        db_number = data['db_number']
        if data['shipping_name'] in ['虚仓电商', '直邮电商', '贝海直邮电商']:
            msg = {'BillCode': db_number}
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            sess = aiohttp.ClientSession(loop=loop)
            xloboapi = getXloboAPI(sess)
            result = loop.run_until_complete(xloboapi.deleteDBNumber(msg))
            loop.close()
            logger.debug('XloboDeleteDBNumber: %s', result)
            # 不检查异常了, 直接默认删除成功
            # if result['Result']['ErrorCount'] > 0:
            #     errmsg = {
            #         'errmsg':
            #         result['Result']['ErrorInfoList'][0]['ErrorDescription']
            #     }
            #     return Response(
            #         data=errmsg, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            shippingdbObj = ShippingDB.objects.get(id=data['id'])
            shippingdbObj.status = '已删除'
            shippingdbObj.order.filter(status='待发货').update(
                status='需面单', channel_delivery_status='')
            shippingdbObj.order.all().update(shippingdb=None)
            shippingdbObj.save(update_fields=[
                'status',
            ])

        return Response(status=status.HTTP_200_OK)


def getInvoiceInfo(db_type, result):
    merger = PdfFileMerger()
    pdftool = utils.PDFTool()
    sqls = {
        'shipping':
        'select p.name, p.specification, o.jancode, o.quantity, s.location, o.seller_memo, o.real_price*o.quantity pay from stock_order o inner join stock_product p on o.jancode=p.jancode inner join stock_stock s on s.product_id=p.id where o.shippingdb_id=%s and s.inventory_id=%s',
        'transform':
        'select p.name,p.specification, p.jancode, poi.quantity,s.location,"",0 from stock_purchaseorderitem poi inner join stock_product p on poi.product_id=p.id inner join stock_stock s on s.product_id=p.id where poi.status="转运中" and poi.transformdb_id=%s and s.inventory_id=%s',
    }
    ptype = 'xlobo' if 'DB' in result[0]['BillCode'].upper() else 'ems'
    for i, b in enumerate(result):
        ordsData = None

        with connection.cursor() as c:
            dbObj = ShippingDB.objects.get(
                db_number=b['BillCode']
            ) if db_type != 'transform' else TransformDB.objects.get(
                db_number=b['BillCode'])
            c.execute(sqls[db_type], (dbObj.id, dbObj.inventory.id))
            ordsData = c.cursor.fetchall()
        if ptype == 'xlobo':
            merger.append(b['BillPdfLabel'], pages=(0, 1))  # 贝海的面单会莫名其妙出现配货单
        else:
            merger.append(b['BillPdfLabel'])
        merger.append(
            BytesIO(pdftool.createShippingPDF(b['BillCode'], ordsData, ptype)))

    res = BytesIO()
    merger.write(res)
    result = {
        'Result': [
            {
                'BillPdfLabel': base64.b64encode(res.getvalue())
            },
        ]
    }
    res.close()

    return result


class XloboGetPDF(views.APIView):
    def get(self, request, format=None):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop = asyncio.get_event_loop()

        # construct api msg
        # drf can't get query list
        # data = {'BillCodes': request.query_params.get('BillCodes[]')}
        data = {'BillCodes': self.request.GET.getlist("BillCodes[]")}
        db_type = request.query_params.get('db_type')
        # data = {
        #     'BillCodes': [
        #         'DB273208811JP',
        #     ]
        # }

        sess = aiohttp.ClientSession(loop=loop)
        xloboapi = getXloboAPI(sess)
        result = loop.run_until_complete(xloboapi.getPDF(data))
        loop.close()
        logger.debug('XloboGetPDF: %s, User input: %s: ',
                     result['ErrorInfoList'], data)
        if result['ErrorCount'] > 0:
            info = result['ErrorInfoList']
            msg = []
            idmis = []
            for i in info:
                db_number = i['Identity']
                if i['ErrorCode'] == 'xlobo.bill.param_not_upload_id':
                    ShippingDB.objects.filter(db_number=db_number).update(
                        print_status='身份证异常')
                    idmis.append(db_number)
                msg.append(db_number + ':' + i['ErrorDescription'])
            raise APIException({'errmsg': '|'.join(msg), 'idmis': idmis})

        result = result['Result']
        for i, b in enumerate(result):
            db_bytes = BytesIO(base64.b64decode(b['BillPdfLabel']))
            result[i]['BillPdfLabel'] = db_bytes

        r = getInvoiceInfo(db_type, result)

        # update shippingdb/transformdb print_status
        if db_type != 'transform':
            ShippingDB.objects.filter(db_number__in=data['BillCodes']).update(
                print_status='已打印',
                print_ts=arrow.now().format('YYYYMMDDHHmmss'))
        else:
            TransformDB.objects.filter(db_number__in=data['BillCodes']).update(
                print_status='已打印',
                print_ts=arrow.now().format('YYYYMMDDHHmmss'))

        return Response(data=r, status=status.HTTP_200_OK)
        # response = HttpResponse(content_type='application/pdf')
        # # response[
        # #     'Content-Disposition'] = 'attachment; filename="somefilename.pdf"'
        # response['Content-Disposition'] = 'inline; filename="somefilename.pdf"'
        # pdf = res.getvalue()
        # res.close()
        # response.write(pdf)
        # return response


class JapanEMSPDF(views.APIView):
    def get(self, request, format=None):
        data = self.request.GET.getlist("BillCodes[]")
        db_type = request.query_params.get('db_type')
        emsStorageDir = getJapanEMSStorageLocal()

        result = []
        for db in data:
            dbFN = os.path.join(emsStorageDir, db + '.pdf')
            r = {
                'BillPdfLabel': PdfFileReader(open(dbFN, 'rb')),
                'BillCode': db,
            }
            result.append(r)

        r = getInvoiceInfo(db_type, result)

        # update shippingdb/transformdb print_status
        if db_type != 'transform':
            ShippingDB.objects.filter(db_number__in=data).update(
                print_status='已打印',
                print_ts=arrow.now().format('YYYYMMDDHHmmss'))
        else:
            TransformDB.objects.filter(db_number__in=data).update(
                print_status='已打印',
                print_ts=arrow.now().format('YYYYMMDDHHmmss'))

        return Response(data=r, status=status.HTTP_200_OK)


class LogisticGet(views.APIView):
    def get(self, request, format=None):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop = asyncio.get_event_loop()

        sess = aiohttp.ClientSession(loop=loop)
        xloboapi = getXloboAPI(sess)
        result = loop.run_until_complete(xloboapi.getLogistic())
        loop.close()
        data = [{
            'value': i['LogisticId'],
            'key': i['LogisticName']
        } for i in result['Result']['LogisticInfoList']
                if i['iCountryId'] == 6]
        return Response(data=data, status=status.HTTP_200_OK)


# 更新洋码头产品库存
class YmatouStockUpdate(views.APIView):
    def post(self, request, format=None):
        # construct api msg
        data = request.data
        product_id = data['product_id']
        seller_name = data['seller_name']

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        sess = aiohttp.ClientSession(
            loop=loop, connector=aiohttp.TCPConnector(verify_ssl=False))
        skey = YMTKEY[seller_name]
        ymtapi = ymatouapi.YmatouAPI(sess, skey['appid'], skey['appsecret'],
                                     skey['authcode'])

        # 获取商品详情
        result = loop.run_until_complete(ymtapi.getProductInfo(product_id))
        for sku in result['content']['product_info']['skus']:
            if not sku['outer_id']:
                continue
            try:
                stockObj = Stock.objects.get(
                    product__jancode=sku['outer_id'], inventory__id=4)
                stock = stockObj.quantity + stockObj.inflight - stockObj.preallocation
                if stock < 0:
                    stock = 0
            except Stock.DoesNotExist:
                stock = 0
            msg = [{
                'outer_sku_id': sku['outer_id'],
                'sku_id': sku['sku_id'],
                'stock_num': stock
            }]
            result = loop.run_until_complete(ymtapi.syncProductStock(msg))
            logger.debug('YmatouStockUpdate: %s', result)
        loop.close()

        return Response(status=status.HTTP_200_OK)
