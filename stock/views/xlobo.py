import asyncio
import base64
import logging
import os.path
from collections import OrderedDict
from io import BytesIO

import aiohttp
from PyPDF2 import PdfFileMerger, PdfFileReader
from django.conf import settings
from django.db import connection, transaction
from django.db.models import F
from rest_framework import status, views
from rest_framework.response import Response

from stock.models import (Inventory, Order, Product, Shipping, ShippingDB,
                          Stock)
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
                errmsg = {'errmsg': '订单已关闭, 请到码头后台确认'}
                return errmsg
            if not disable_checkOrderDelivery:
                if result['content']['order_info']['order_status'] in [3, 4]:
                    errmsg = {'errmsg': '订单已发货, 请到码头后台确认'}
                    return errmsg
            for oi in result['content']['order_info']['order_items_info']:
                if oi['refund_status'] == 0:
                    errmsg = {'errmsg': '订单退款审核中, 请到码头后台确认'}
                    return errmsg
        return None


def checkUserOtherOrder(ords):
    # 如果need_check, 需要先查一下该用户是否有其他订单没有一并提交, 如果有, 返回
    # 异常
    check_ords = Order.objects.filter(
        receiver_name=ords[0]['receiver_name'],
        receiver_mobile=ords[0]['receiver_mobile'],
        shippingdb__isnull=True,
        status__in=['待处理', '待采购', '需面单', '已采购', '需介入'])
    if len(check_ords) != len(ords):
        errmsg = {'errmsg': '该用户有其他订单, 请检查.'}
        return errmsg
    return None


def getJapanEMSStorageLocal():
    return settings.EMS_STORAGE_DIR


# 1. 生成DB面单, 如果是码头订单, 需要先确认订单状态, 状态异常, 直接返回异常
# 2. 需要考虑该用户是否有其他订单, 如果有其他订单, 需要提醒操作人员.
class XloboCreateNoVerification(views.APIView):
    def post(self, request, format=None):
        data = request.data
        ords = data['orders']
        disable_check = data['disable_check']

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop = asyncio.get_event_loop()
        sess = aiohttp.ClientSession(loop=loop)

        ordStatus = checkOrderStatus(loop, sess, ords)
        if ordStatus:
            return Response(data=ordStatus, status=status.HTTP_400_BAD_REQUEST)

        if not disable_check:
            otherOrder = checkUserOtherOrder(ords)
            if otherOrder:
                return Response(
                    data=otherOrder, status=status.HTTP_400_BAD_REQUEST)

        # create db number
        # construct api msg
        channel_name = ords[0]['channel_name']
        address = ords[0]['receiver_address'].split(',')
        order_piad_time = ords[0]['piad_time']
        billSenderInfo = {
            'Name': ords[0]['seller_name'],
            'Address': '中央区新富1-3-15　京橋プリズムビル　４階',
            'Phone': '11',
        }
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

        xloboapi = ymatouapi.XloboAPI(sess, access_token, client_secret,
                                      client_id)
        result = loop.run_until_complete(xloboapi.createNoVerification(data))
        logger.debug('XloboCreateNoVerification: %s', result)
        if result['ErrorCount'] > 0:
            errmsg = {'errmsg': result['ErrorInfoList'][0]['ErrorDescription']}
            return Response(data=errmsg, status=status.HTTP_400_BAD_REQUEST)
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
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop = asyncio.get_event_loop()
        sess = aiohttp.ClientSession(loop=loop)

        ordStatus = checkOrderStatus(loop, sess, ords)
        if ordStatus:
            return Response(data=ordStatus, status=status.HTTP_400_BAD_REQUEST)

        if not disable_check:
            otherOrder = checkUserOtherOrder(ords)
            if otherOrder:
                return Response(
                    data=otherOrder, status=status.HTTP_400_BAD_REQUEST)

        # construct api msg
        channel_name = ords[0]['channel_name']
        address = ords[0]['receiver_address'].split(',')
        order_piad_time = ords[0]['piad_time']
        billSenderInfo = {
            'Name': ords[0]['seller_name'],
            'Address': '中央区新富1-3-15　京橋プリズムビル　４階',
            'Phone': '11',
        }
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

        xloboapi = ymatouapi.XloboAPI(sess, access_token, client_secret,
                                      client_id)
        result = loop.run_until_complete(xloboapi.createFBXBill(data))
        logger.debug('XloboCreateFBXBill: %s', result)
        if result['ErrorCount'] > 0:
            errmsg = {'errmsg': result['ErrorInfoList'][0]['ErrorDescription']}
            return Response(data=errmsg, status=status.HTTP_400_BAD_REQUEST)
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
        tax_included_channel = data['tax_included_channel']

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop = asyncio.get_event_loop()
        sess = aiohttp.ClientSession(loop=loop)

        ordStatus = checkOrderStatus(loop, sess, ords)
        if ordStatus:
            return Response(data=ordStatus, status=status.HTTP_400_BAD_REQUEST)

        if not disable_check:
            otherOrder = checkUserOtherOrder(ords)
            if otherOrder:
                return Response(
                    data=otherOrder, status=status.HTTP_400_BAD_REQUEST)

        # create ems number
        # sendType
        #    EMS(物品): 1 / 国际e包裹: 4 / 国际邮包: 5
        # transType
        #    航空: 1 / 标准航空(SAL): 3 / 海运: 2
        shippingInfo = {
            'EMS': (1, None),
            'EPACK': (1, None),
            'SAL': (5, 3),
            'SURFACE': (5, 2)
        }
        sendType = shippingInfo[ords[0]['shipping_name']][0]
        transType = shippingInfo[ords[0]['shipping_name']][1]
        ems_number = japanems.createJapanEMS(ords[0], sendType, transType)

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
                inventory=inventoryObj)
            shippingdbObj.save()
            for o in ords:
                orderObj = Order.objects.get(id=o['id'])
                orderObj.shippingdb = shippingdbObj
                if orderObj.status == '需面单':
                    orderObj = '待发货'
                orderObj.save(update_fields=['shippingdb', 'status'])

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
        sess = aiohttp.ClientSession(loop=loop)

        ordStatus = checkOrderStatus(loop, sess, ords,
                                     disable_checkOrderDelivery)
        if ordStatus:
            return Response(data=ordStatus, status=status.HTTP_400_BAD_REQUEST)

        if not disable_check:
            otherOrder = checkUserOtherOrder(ords)
            if otherOrder:
                return Response(
                    data=otherOrder, status=status.HTTP_400_BAD_REQUEST)

        db_number = request.data['Comment']
        channel_name = ords[0]['channel_name']
        order_piad_time = ords[0]['piad_time']
        # delivery_type = ords[0]['delivery_type']
        with transaction.atomic():
            orderStatus = None
            shippingdbObj = None
            try:
                shippingdbObj = ShippingDB.objects.get(db_number=db_number)
                for o in ords:
                    if '拼邮' not in o['delivery_type']:
                        errmsg = {'errmsg': '非拼邮订单, 面单号被重复使用, 请仔细检查确认'}
                        return Response(
                            data=errmsg, status=status.HTTP_400_BAD_REQUEST)
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
                if disable_channel_delivery:
                    orderObj.channel_delivery_status = '已发货'
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
            xloboapi = ymatouapi.XloboAPI(sess, access_token, client_secret,
                                          client_id)
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
            shippingdbObj.order.filter(status='待发货').update(status='需面单')
            shippingdbObj.order.all().update(shippingdb=None)
            shippingdbObj.save(update_fields=[
                'status',
            ])

        return Response(status=status.HTTP_200_OK)


class XloboGetPDF(views.APIView):
    def get(self, request, format=None):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop = asyncio.get_event_loop()

        # construct api msg
        # drf can't get query list
        # data = {'BillCodes': request.query_params.get('BillCodes[]')}
        data = {'BillCodes': self.request.GET.getlist("BillCodes[]")}
        # data = {
        #     'BillCodes': [
        #         'DB273208811JP',
        #     ]
        # }

        sess = aiohttp.ClientSession(loop=loop)
        xloboapi = ymatouapi.XloboAPI(sess, access_token, client_secret,
                                      client_id)
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
            errmsg = {'errmsg': '|'.join(msg), 'idmis': idmis}
            return Response(data=errmsg, status=status.HTTP_400_BAD_REQUEST)
        merger = PdfFileMerger()
        pdftool = utils.PDFTool()
        sql = 'select p.name, p.specification, o.jancode, o.quantity, s.location, o.seller_memo from stock_order o inner join stock_product p on o.jancode=p.jancode inner join stock_stock s on s.product_id=p.id where o.shippingdb_id=%s and s.inventory_id=%s'
        for i, b in enumerate(result['Result']):
            db_bytes = base64.b64decode(b['BillPdfLabel'])
            ordsData = None

            with connection.cursor() as c:
                shippingdbObj = ShippingDB.objects.get(db_number=b['BillCode'])
                c.execute(sql, (shippingdbObj.id, shippingdbObj.inventory.id))
                # c.execute(sql, (8, ))
                ordsData = c.cursor.fetchall()
            # inp2 = BytesIO(pdftool.createShippingPDF(b['BillCode'], ordsData))
            # inp2 = open(
            #     '/home/tacy/workspace/python/lelewu/ymatou/simple_table.pdf',
            #     'rb')
            if not i:
                merger.append(fileobj=BytesIO(db_bytes), pages=(0, 1))
            else:
                merger.merge(
                    position=i * 2 + 1,
                    fileobj=BytesIO(db_bytes),
                    pages=(0, 1))
            merger.merge(
                position=2**(i + 1),
                fileobj=BytesIO(
                    pdftool.createShippingPDF(b['BillCode'], ordsData)),
                pages=(0, 1))

        res = BytesIO()
        merger.write(res)
        result['Result'] = [
            {
                'BillPdfLabel': base64.b64encode(res.getvalue())
            },
        ]
        res.close()

        # update shippingdb print_status
        ShippingDB.objects.filter(db_number__in=data['BillCodes']).update(
            print_status='已打印')

        return Response(data=result, status=status.HTTP_200_OK)
        # response = HttpResponse(content_type='application/pdf')
        # # response[
        # #     'Content-Disposition'] = 'attachment; filename="somefilename.pdf"'
        # response['Content-Disposition'] = 'inline; filename="somefilename.pdf"'
        # pdf = res.getvalue()
        # res.close()
        # response.write(pdf)
        # return response


class getJapanEMSPDF(views.APIView):
    def get(self, request, format=None):
        data = self.request.GET.getlist("BillCodes[]")
        emsStorageDir = getJapanEMSStorageLocal()

        result = [{'BillPdfLabel': db + '.pdf', 'BillCode': db} for db in data]

        merger = PdfFileMerger()
        pdftool = utils.PDFTool()
        sql = 'select p.name, p.specification, o.jancode, o.quantity, s.location, o.seller_memo from stock_order o inner join stock_product p on o.jancode=p.jancode inner join stock_stock s on s.product_id=p.id where o.shippingdb_id=%s and s.inventory_id=%s'
        for i, b in enumerate(result):
            ordsData = None
            with connection.cursor() as c:
                shippingdbObj = ShippingDB.objects.get(db_number=b['BillCode'])
                c.execute(sql, (shippingdbObj.id, shippingdbObj.inventory.id))
                ordsData = c.cursor.fetchall()

            dbFN = os.path.join(emsStorageDir, b['BillPdfLabel'])
            merger.append(PdfFileReader(open(dbFN, 'rb')))
            merger.append(
                BytesIO(pdftool.createShippingPDF(b['BillCode'], ordsData)))

        res = BytesIO()
        merger.write(res)
        result = {
            'Result': [{
                'BillPdfLabel': base64.b64encode(res.getvalue())
            }]
        }
        res.close()

        # update shippingdb print_status
        ShippingDB.objects.filter(db_number__in=data).update(
            print_status='已打印')

        return Response(data=result, status=status.HTTP_200_OK)


class LogisticGet(views.APIView):
    def get(self, request, format=None):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop = asyncio.get_event_loop()

        sess = aiohttp.ClientSession(loop=loop)
        xloboapi = ymatouapi.XloboAPI(sess, access_token, client_secret,
                                      client_id)
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
        sess = aiohttp.ClientSession(loop=loop)
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
                msg = [{
                    'outer_sku_id': sku['outer_id'],
                    'sku_id': sku['sku_id'],
                    'stock_num': stock
                }]
                result = loop.run_until_complete(ymtapi.syncProductStock(msg))
                logger.debug('YmatouStockUpdate: %s', result)
            except Stock.DoesNotExist:
                continue
        loop.close()

        return Response(status=status.HTTP_200_OK)
