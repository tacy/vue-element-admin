import base64
import asyncio
import logging
from collections import OrderedDict
from io import BytesIO

import aiohttp
from PyPDF2 import PdfFileMerger
from django.db import connection, transaction
from django.db.models import F
from rest_framework import status, views
from rest_framework.response import Response

from stock.models import (Inventory, Order, Product, Shipping, ShippingDB,
                          Stock)
from ymatou import utils, ymatouapi

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


# 1. 生成DB面单, 如果是码头订单, 需要先确认订单状态, 状态异常, 直接返回异常
# 2. 需要考虑该用户是否有其他订单, 如果有其他订单, 需要提醒操作人员.
class XloboCreateNoVerification(views.APIView):
    def post(self, request, format=None):
        data = request.data
        ords = data['orders']

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop = asyncio.get_event_loop()
        sess = aiohttp.ClientSession(loop=loop)

        # ymatou order need check orderstatus
        # 这里可能有合并订单发货情况, 需要根据订单ID去重, 然后去码头后台查每一
        # 个订单状态是否正常
        if '洋码头' in ords[0]['channel_name']:
            skey = YMTKEY[ords[0]['seller_name']]
            ymtapi = ymatouapi.YmatouAPI(sess, skey['appid'],
                                         skey['appsecret'], skey['authcode'])
            ordids = list([OrderedDict.fromkeys([i['orderid'] for i in ords])])
            for oid in ordids:
                result = loop.run_until_complete(
                    ymtapi.getOrderInfo(ords[0]['orderid']))
                # result = loop.run_until_complete(ymtapi.getOrderInfo('127086025'))
                if result['content']['order_info']['order_status'] in [
                        12, 13, 14
                ]:
                    errmsg = {'errmsg': '订单已关闭, 请到码头后台确认'}
                    return Response(
                        data=errmsg, status=status.HTTP_400_BAD_REQUEST)
                for oi in result['content']['order_info']['order_items_info']:
                    if oi['refund_id'] == 0:
                        errmsg = {'errmsg': '订单退款审核中, 请到码头后台确认'}
                        return Response(
                            data=errmsg, status=status.HTTP_400_BAD_REQUEST)

        # 如果need_check, 需要先查一下该用户是否有其他订单没有一并提交, 如果有, 返回
        # 异常
        if not data['disable_check']:
            check_ords = Order.objects.filter(
                receiver_name=ords[0]['receiver_name'],
                receiver_mobile=ords[0]['receiver_mobile'],
                shippingdb__isnull=True,
                status__in=['待处理', '待采购', '待发货', '已采购', '需介入'])
            if len(check_ords) != len(ords):
                errmsg = {'errmsg': '该用户有其他订单, 请检查.'}
                return Response(
                    data=errmsg, status=status.HTTP_400_BAD_REQUEST)

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
                orderObj.save(update_fields=['shippingdb'])

        return Response(data=result, status=status.HTTP_200_OK)


# 虚仓电商无需我们自己再处理, 直接贝海负责打包发货
class XloboCreateFBXBill(views.APIView):
    def post(self, request, format=None):
        data = request.data
        ords = data['orders']
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

        # ymatou order need check orderstatus
        # 这里可能有合并订单发货情况, 需要根据订单ID去重, 然后去码头后台查每一
        # 个订单状态是否正常
        if '洋码头' in ords[0]['channel_name']:
            skey = YMTKEY[ords[0]['seller_name']]
            ymtapi = ymatouapi.YmatouAPI(sess, skey['appid'],
                                         skey['appsecret'], skey['authcode'])
            ordids = list([OrderedDict.fromkeys([i['orderid'] for i in ords])])
            for oid in ordids:
                result = loop.run_until_complete(
                    ymtapi.getOrderInfo(ords[0]['orderid']))
                # result = loop.run_until_complete(ymtapi.getOrderInfo('127086025'))
                if result['content']['order_info']['order_status'] in [
                        12, 13, 14
                ]:
                    errmsg = {'errmsg': '订单已关闭, 请到码头后台确认'}
                    return Response(
                        data=errmsg, status=status.HTTP_400_BAD_REQUEST)
                for oi in result['content']['order_info']['order_items_info']:
                    if oi['refund_id'] == 0:
                        errmsg = {'errmsg': '订单退款审核中, 请到码头后台确认'}
                        return Response(
                            data=errmsg, status=status.HTTP_400_BAD_REQUEST)

        # 如果need_check, 需要先查一下该用户是否有其他订单没有一并提交, 如果有, 返回
        # 异常
        if not data['disable_check']:
            check_ords = Order.objects.filter(
                receiver_name=ords[0]['receiver_name'],
                receiver_mobile=ords[0]['receiver_mobile'],
                shippingdb__isnull=True,
                status__in=['待处理', '待采购', '待发货', '已采购', '需介入'])
            if len(check_ords) != len(ords):
                errmsg = {'errmsg': '该用户有其他订单, 请检查.'}
                return Response(
                    data=errmsg, status=status.HTTP_400_BAD_REQUEST)

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
            info = result['ErrorInfoList'][0]
            errmsg = {
                'errmsg': info['Identity'] + ':' + info['ErrorDescription']
            }
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


# 思考: 拼邮订单, 还是需要填写正确的EMS单号, 否则不容易追踪包裹情况, 但是存在
# 不正确填写EMS单号的情况, 这个需要怎么处理?
class ManualAllocateDBNumber(views.APIView):
    def post(self, request, format=None):
        ords = request.data['orders']

        # ymatou order need check orderstatus
        if '洋码头' in ords[0]['channel_name']:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop = asyncio.get_event_loop()
            sess = aiohttp.ClientSession(loop=loop)

            skey = YMTKEY[ords[0]['seller_name']]
            ymtapi = ymatouapi.YmatouAPI(sess, skey['appid'],
                                         skey['appsecret'], skey['authcode'])
            ordids = list([OrderedDict.fromkeys([i['orderid'] for i in ords])])
            for oid in ordids:
                result = loop.run_until_complete(
                    ymtapi.getOrderInfo(ords[0]['orderid']))
                # result = loop.run_until_complete(ymtapi.getOrderInfo('127086025'))
                if result['content']['order_info']['order_status'] in [
                        12, 13, 14
                ]:
                    errmsg = {'errmsg': '订单已关闭, 请到码头后台确认'}
                    return Response(
                        data=errmsg, status=status.HTTP_400_BAD_REQUEST)
                for oi in result['content']['order_info']['order_items_info']:
                    if oi['refund_id'] == 0:
                        errmsg = {'errmsg': '订单退款审核中, 请到码头后台确认'}
                        return Response(
                            data=errmsg, status=status.HTTP_400_BAD_REQUEST)

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
                    if '拼邮' not in o['shipping_name']:
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
                if '拼邮' in shippingObj.name:  # 拼邮不进入待发货列表, 但是需打包发货
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
                orderObj.save(update_fields=['shippingdb', 'status'])

        return Response(status=status.HTTP_200_OK)
