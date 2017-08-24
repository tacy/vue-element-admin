import asyncio
import json
import logging
import random
import string

import aiohttp
import arrow.arrow
import django_filters.rest_framework
from django.db import connection, transaction
from django.db.models import F
from rest_framework import generics, status, views
from rest_framework.authtoken.models import Token
from rest_framework.response import Response

from .filter import OrderFilter
from .models import (Inventory, Order, Product, PurchaseOrder,
                     PurchaseOrderItem, Shipping, ShippingDB, Stock, Supplier)
from .serializers import (
    InventorySerializer, OrderSerializer, ProductSerializer,
    PurchaseOrderItemSerializer, PurchaseOrderSerializer, ShippingDBSerializer,
    ShippingSerializer, StockSerializer, SupplierSerializer, TokenSerializer)
from ymatou import uex, ymatouapi

access_token = 'AESaZpmFNNcLRbNFmWK38S2ELvpzwjHkRjkpJkNmaaRIpEJ7T+FYBfVvoekui/2k1g=='
client_secret = 'APvYM8Mt5Xg1QYvker67VplTPQRx28Qt/XPdY9D7TUhaO3vgFWQ71CRZ/sLZYrn97w=='.lower(
)
client_id = '8417db83-360c-4275-974f-cf9a2734d8f8'
uex_user = '2830020@qq.com'
uex_passwd = '20162017'

# debug
# access_token = 'ACiYUZ6aKC48faYFD6MpvbOf73BdE9OV5g15q1A6Ghs+i/XIawq/9RHJCzc6Y3UNxA=='
# client_secret = 'APvYM8Mt5Xg1QYvker67VplTPQRx28Qt/XPdY9D7TUhaO3vgFWQ71CRZ/sLZYrn97w=='.lower(
# )
# client_id = '68993573-E38D-4A8A-A263-055C401F9369'

logger = logging.getLogger(__name__)


class XloboCreateNoVerification(views.APIView):
    def post(self, request, format=None):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop = asyncio.get_event_loop()

        # construct api msg
        data = request.data
        ords = data['orders']
        channel_name = ords[0]['channel_name']
        address = ords[0]['receiver_address'].split(',')
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

        sess = aiohttp.ClientSession(loop=loop)
        xloboapi = ymatouapi.XloboAPI(sess, access_token, client_secret,
                                      client_id)
        result = loop.run_until_complete(xloboapi.createNoVerification(data))
        logger.debug('XloboCreateNoVerification', result)
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

        # construct api msg
        data = request.data
        ords = data['orders']
        channel_name = ords[0]['channel_name']
        address = ords[0]['receiver_address'].split(',')
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
        sess = aiohttp.ClientSession(loop=loop)
        xloboapi = ymatouapi.XloboAPI(sess, access_token, client_secret,
                                      client_id)
        result = loop.run_until_complete(xloboapi.createFBXBill(data))
        logger.debug('XloboCreateFBXBill', result)
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
                    jancode=orderObj.jancode, inventory=orderObj.inventory)
                stockObj.quantity = F('quantity') - orderObj.quantity  # 扣减库存
                stockObj.preallocation = F('preallocation') - orderObj.quantity
                stockObj.save()

        return Response(data=result, status=status.HTTP_200_OK)


class XloboGetPDF(views.APIView):
    def get(self, request, format=None):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop = asyncio.get_event_loop()
        # construct api msg
        data = {
            'BillCodes': [
                request.query_params.get('BillCode'),
            ]
        }
        data = {
            'BillCodes': [
                'DB273208811JP',
            ]
        }

        sess = aiohttp.ClientSession(loop=loop)
        xloboapi = ymatouapi.XloboAPI(sess, access_token, client_secret,
                                      client_id)
        result = loop.run_until_complete(xloboapi.getPDF(data))
        loop.close()
        logger.debug('XloboGetPDF', result)
        if result['ErrorCount'] > 0:
            errmsg = {'errmsg': result['ErrorInfoList'][0]['ErrorDescription']}
            return Response(data=errmsg, status=status.HTTP_400_BAD_REQUEST)
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


class UexStockOut(views.APIView):
    def post(self, request, format=None):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        data = request.data
        ords = data['orders']
        channel_name = ords[0]['channel_name']
        address = ords[0]['receiver_address'].split(',')
        # construct api msg
        payload = {
            'ship_id': data['ship_id'],
            'add_server[0]': 1,
            'user_order_no': ords[0]['orderid'],
            'send_user': ords[0]['seller_name'],
            'address[consignee]': ords[0]['receiver_name'],
            'address[phone]': ords[0]['receiver_mobile'],
            'address[card]': ords[0]['receiver_idcard'],
            'address[province]': address[0],
            'address[city]': address[1],
            'address[district]': address[2],
            'address[address]': address[3],
        }
        for i, v in enumerate(ords):
            payload['goods[' + str(i) + '][jan_code]'] = v['jancode']
            payload['goods[' + str(i) + '][num]'] = v['quantity']

        sess = aiohttp.ClientSession(loop=loop)
        uexapi = uex.UexAPI(sess, uex_user, uex_passwd)
        result = loop.run_until_complete(uexapi.login())
        result = loop.run_until_complete(uexapi.stockOut(payload))
        loop.close()
        logger.debug('UexStockOut', result)
        result = json.loads(result)
        if not result['code']:
            errmsg = {'errmsg': result['msg']}
            return Response(data=errmsg, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            shippingObj = Shipping.objects.get(id=ords[0]['shipping'])
            inventoryObj = Inventory.objects.get(id=ords[0]['inventory'])
            shippingdbObj = ShippingDB(
                db_number=result['order_sn'],
                status='已出库',
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
                    jancode=orderObj.jancode, inventory=orderObj.inventory)
                stockObj.quantity = F('quantity') - orderObj.quantity  # 扣减库存
                stockObj.preallocation = F('preallocation') - orderObj.quantity
                stockObj.save()
        return Response(data=result, status=status.HTTP_200_OK)


class ManualAllocateDBNumber(views.APIView):
    def post(self, request, format=None):
        ords = request.data['orders']
        db_number = request.data['Comment']
        channel_name = ords[0]['channel_name']
        with transaction.atomic():
            shippingObj = Shipping.objects.get(id=ords[0]['shipping'])
            inventoryObj = Inventory.objects.get(id=ords[0]['inventory'])
            shippingdbObj = ShippingDB(
                db_number=db_number,
                status='待处理',
                channel_name=channel_name,
                shipping=shippingObj,
                inventory=inventoryObj)
            shippingdbObj.save()
            for o in ords:
                orderObj = Order.objects.get(id=o['id'])
                orderObj.shippingdb = shippingdbObj
                orderObj.save(update_fields=['shippingdb'])

        return Response(status=status.HTTP_200_OK)


# 订单发货
class StockOut(views.APIView):
    # 1. 标记db面单状态;
    # 2. 标记订单状态
    # 3. 扣减库存
    def post(self, request, format=None):
        shippingdb_id = request.data['shippingdb_id']
        with transaction.atomic():
            shippingdbObj = ShippingDB.objects.get(id=shippingdb_id)
            shippingdbObj.status = '已出库'
            shippingdbObj.save(update_fields=['status'])
            for o in shippingdbObj.order.all():
                o.status = '已发货'
                o.save(update_fields=['status'])
                stockObj = Stock.objects.get(
                    jancode=o.jancode, inventory=o.inventory)
                stockObj.quantity = F('quantity') - o.quantity
                stockObj.preallocation = F('preallocation') - o.quantity
                stockObj.save()

        return Response(status=status.HTTP_200_OK)


class OrderItemGet(views.APIView):
    def get(self, request, format=None):
        sql = (
            'select o.orderid orderid, o.jancode jancode, o.product_title product_title, '
            'o.sku_properties_name sku_properties_name, o.quantity quantity, '
            'o.receiver_name receiver_name, o.receiver_address receiver_address, '
            'o.receiver_mobile receiver_mobile, s.location location, sdb.db_number db_number '
            'from stock_order o inner join stock_stock s '
            'on o.jancode=s.jancode and o.inventory_id=s.inventory_id and o.shippingdb_id=%s '
            'inner join stock_shippingdb sdb on o.shippingdb_id=sdb.id')

        def dictfetchall(cursor):
            "Return all rows from a cursor as a dict"
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

        db_number = request.query_params.get('shippingdb_id')
        print(request.query_params)
        with connection.cursor() as c:
            c.execute(sql, (db_number, ))
            results = dictfetchall(c)
            data = {
                'results': results,
            }
            # print(data)
            return Response(data=data, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class CategoryGet(views.APIView):
    def get(self, request, format=None):
        sql = 'select b.category_id category_id, b.category_cn_name category_cn_name, a.category_id category_parent_id, a.category_cn_name category_parent_cn_name, a.category_version category_version from stock_category a join stock_category b on (a.category_id=b.category_parent_id)'

        def dictfetchall(cursor):
            "Return all rows from a cursor as a dict"
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

        with connection.cursor() as c:
            c.execute(sql)
            results = dictfetchall(c)
            relationData = {}
            for i in results:
                dictkey = i['category_parent_id'].zfill(5)
                if dictkey in relationData:
                    relationData[dictkey]['children'].append({
                        'label':
                        i['category_cn_name'],
                        'value':
                        i['category_id']
                    })
                else:
                    relationData[dictkey] = {
                        'label':
                        i['category_parent_cn_name'],
                        'value':
                        i['category_parent_id'],
                        'children': [
                            {
                                'label': i['category_cn_name'],
                                'value': i['category_id']
                            },
                        ]
                    }

            sortData = [relationData[i] for i in sorted(relationData.keys())]
            data = {
                'results': sortData,
            }
            # print(data)
            return Response(data=data, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)


# 录入订单
class OrderTPRCreate(views.APIView):
    def put(self, request, format=None):
        data = request.data
        t = arrow.now()
        piad_time = t.format('YYYY-MM-DD HH:mm:ss')
        orderid = 'T' + t.format('YYMMDD') + ''.join(
            random.choices(string.digits, k=2))
        with transaction.atomic():
            for p in data['products']:
                o = {
                    'orderid': orderid,
                    'piad_time': piad_time,
                    'delivery_type': '第三方',
                    'seller_name': data['seller_name'],
                    'channel_name': data['channel_name'],
                    'receiver_name': data['receiver_name'],
                    'receiver_address': data['receiver_address'],
                    'receiver_zip': data['receiver_zip'],
                    'receiver_mobile': data['receiver_mobile'],
                    'receiver_idcard': data['receiver_idcard'],
                    'seller_memo': data['seller_memo'],
                    'jancode': p['jancode'],
                    'product_title': p['product_title'],
                    'sku_properties_name': p['sku_properties_name'],
                    'price': p['price'],
                    'quantity': p['quantity']
                }
                orderObj = Order(**o)
                orderObj.save()
        return Response(status=status.HTTP_200_OK)


# 订单预处理
class OrderAllocate(views.APIView):

    # 派单需要的操作: 1. 占用库存(preallocation); 2. 标记订单需要采购的数量(need_purchase); 3. 修改订单状态(status:待发货/待采购)
    #
    # 派单流程: 派单分为派单和重派, 如果订单的inventory字段为空, 定位为派单;
    # 如果该字段非空, 定义为重派.
    #
    # 需要根据传入订单号, 查询数据库表中对应订单, 判断order_inventory字段内容:
    # if paramorder.status == '已删除'; then delete order opetion, use in conflict
    # if paramorder.inventory is null; then return
    # if dborder.inventory is null; then 派单
    # if dborder.inventory != paramorder.inventory; then 重派
    # if dborder.inventory == paramorder.inventory:
    #     if dborder.shipping == paramorder.shipping; then return
    #     if dborder.shipping != paramorder.shipping; then (仅仅更新order数据, 无需更新库存信息)
    #
    # update order status
    # if stock(quantity+inflight-preallocation) > 0: 待发货 else 采购
    #
    # 派单需要更新库存占库字段; 重派需要先从之前指派的仓库回滚占库数据, 再更新库存占
    # 库字段;
    #
    # TODO: 需要注意, 订单派单之后, 不能再修改订单jancode, 这个问题后面fix
    #
    def put(self, request, format=None):
        orderInfo = request.data
        allocate_time = arrow.now().format('YYYY-MM-DD HH:mm:ss')
        paramInventory = orderInfo['inventory']
        relate_inventory = Inventory.objects.get(id=paramInventory)
        # if not paramInventory or not paramShipping:  # 传入参数为空, 无效
        #     return status.HTTP_400_BAD_REQUEST
        productObj = None
        try:
            productObj = Product.objects.get(jancode=orderInfo['jancode'])
        except Product.DoesNotExist:
            results = {'errmsg': '商品库中无该商品, 请先创建产品资料'}
            return Response(data=results, status=status.HTTP_400_BAD_REQUEST)
        stockObj = None
        try:
            stockObj = Stock.objects.get(
                inventory=paramInventory, jancode=productObj)
        except Stock.DoesNotExist:  # 如果第一次分配到该仓库, 主动在该仓库新建产品记录
            stockObj = Stock(
                jancode=productObj,
                inventory=relate_inventory,
                quantity=0,
                inflight=0,
                preallocation=0)
            stockObj.save()
        dborder = Order.objects.get(id=orderInfo['id'])
        dbinventory = dborder.inventory

        rollbackstock = ''
        isStockUpdate = True
        # 计算库存变化
        if not dbinventory:  # 派单
            stockObj.preallocation = F(
                'preallocation') + orderInfo['quantity']  # 分配订单需要占库存
        else:  # 重新派单
            if dbinventory.id != paramInventory:  # 重派单, 订单派给了新的仓库, 需要回滚之前的库存占用
                rollbackstock = Stock.objects.get(
                    inventory=dbinventory.id, jancode=productObj)
                rollbackstock.preallocation = F(
                    'preallocation') - orderInfo['quantity']
                stockObj.preallocation = F(
                    'preallocation') + orderInfo['quantity']
            else:  # 重派单, 但是仓库没有改变, 无需对库存做更新
                if dborder.shipping == orderInfo[
                        'shipping']:  # 派单信息没有变化, 无需处理.
                    return status.HTTP_200_OK
                isStockUpdate = False

        with transaction.atomic():
            # 计算订单状态
            if isStockUpdate:
                # if not stockInfo['inflight']:
                #     stockInfo['inflight'] = 0
                stockObj.save()
                # 使用F操作models, save之后需要从数据库刷新, 否则值不能使用
                stockObj.refresh_from_db()

                orderInfo[
                    'allocate_time'] = allocate_time  # 如果更新库存表, 就需要更新派单时间

                purchaseQuantity = stockObj.preallocation - (
                    stockObj.quantity + stockObj.inflight)
                if purchaseQuantity > 0:  # 订单需采购
                    orderInfo['need_purchase'] = purchaseQuantity
                    orderInfo['status'] = '待采购'
                else:
                    orderInfo['status'] = '待发货'

            # 更新订单和仓库信息
            # relate_inventory = Inventory.objects.get(id=orderInfo['inventory'])
            relate_shipping = Shipping.objects.get(id=orderInfo['shipping'])
            # relate_purchaseorder = PurchaseOrder.objects.get(
            #     id=orderInfo['purchaseorder'])
            orderInfo['inventory'] = relate_inventory
            orderInfo['shipping'] = relate_shipping
            # orderInfo['purchaseorder'] = relate_purchaseorder

            # question: how to serializ dict
            orderInfo.pop('inventory_name')
            orderInfo.pop('shipping_name')
            o = Order(**orderInfo)
            o.save()

            if rollbackstock:
                rollbackstock.save()
            return Response(status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_BAD_REQUEST)


# 获取采购列表
class OrderPurchaseList(views.APIView):
    # TODO: 分页
    # 需要返回查询时间, 创建采购单的时候, 我们需要用这个时间来和订单的派单时间做对比, 看看是否能关联相关订单
    #
    def get(self, request, format=None):
        sql = "select s.jancode, s.name product_name, s.specification sku_properties_name, sum(o.need_purchase) qty from stock_product s inner join stock_order o on o.jancode=s.jancode and o.status='待采购' and o.inventory_id=%s group by jancode"

        def dictfetchall(cursor):
            "Return all rows from a cursor as a dict"
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

        inventory = request.query_params.get('inventory')
        with connection.cursor() as c:
            c.execute(sql, [inventory])
            results = dictfetchall(c)
            print(inventory, results, request.query_params)
            data = {
                'data': results,
                'queryTime': arrow.now().format('YYYY-MM-DD HH:mm:ss')
            }
            print(data)
            return Response(data=data, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)


# 生成采购单
class OrderPurchase(views.APIView):
    # TODO: 分页 / 限制只能多采不能少采
    #
    # 流程:
    #   1. 根据注文编号(purchaseorderid)生成purchaseorder.
    #   2. 同时生成purchaseitem.
    #   3. 标记关联订单状态:已采购, 并标注关联purchaseorder. (这里需要考虑采购和派单同时进行情况, 关联订单时需要比较时间)
    #   4. 修改关联库存记录, 增加在途库存.
    #
    def put(self, request, format=None):
        print(request.data)
        data = request.data.get('data')
        queryTime = request.data.get('queryTime')
        inventory = request.data.get('inventory')

        with transaction.atomic():
            createtime = arrow.now()
            pos = {}
            for i in data:
                # create purchaseorder
                po_id = i.get('purchaseorderid')
                if not po_id:
                    continue
                if (not i['quantity'] or i['quantity'] < i['qty'] or
                        not i['supplier'] or not i['price']):
                    results = {'errmsg': '请检查输入'}
                    return Response(
                        data=results, status=status.HTTP_400_BAD_REQUEST)
                jancode = i['jancode']
                if po_id not in pos:
                    supplierOb = Supplier.objects.get(id=i['supplier'])
                    inventoryOb = Inventory.objects.get(id=inventory)
                    po = PurchaseOrder(
                        orderid=po_id,
                        supplier=supplierOb,
                        inventory=inventoryOb,
                        create_time=createtime,
                        status='在途', )
                    po.save()
                    pos[po_id] = po

                # add purchase item
                price = i['price']
                poitem = PurchaseOrderItem(
                    jancode=Product.objects.get(jancode=jancode),
                    quantity=i['quantity'],
                    purchaseorder=pos[po_id],
                    price=price)
                poitem.save()

                # set inflight in stock
                stock = Stock.objects.get(inventory=inventory, jancode=jancode)
                stock.inflight = F('inflight') + int(i['quantity'])
                stock.save()

                # 1. update order, notes: may qty != quantity
                # 2. if allocate_time > querytime, don't relation it.
                orders = Order.objects.filter(
                    inventory=inventory, jancode=jancode, status='待采购')
                # orders_qty_sum = 0
                for o in orders:
                    # django存的是naive的时间, 所以我们这里也要用才能比较
                    if o.allocate_time > arrow.get(queryTime).naive:
                        continue
                    o.purchaseorder = pos[po_id]
                    o.status = '已采购'
                    o.save(update_fields=['status', 'purchaseorder'])
                    # orders_qty_sum += o.need_purchase
                    # if orders_qty_sum > int(i['quantity']):
                    #     break

            return Response(status=status.HTTP_201_CREATED)


# 提交采购单(直接采购, 不参考待采购列表)
class NoOrderPurchase(views.APIView):
    #
    # 流程:
    #   1. 根据注文编号(orderid)生成purchaseorder.
    #   2. 同时生成purchaseitem.
    #   3. 标记关联订单状态:已采购, 并标注关联purchaseorder ( 如果有的话, 需要关联, 可以减少重复采购 ).
    #   4. 修改关联库存记录, 增加在途库存.
    #   postForm: {
    #   inventory: undefined,
    #   supplier: undefined,
    #   orderid: '',
    #   items: [
    #     {
    #       jancode: undefined,
    #       quantity: undefined,
    #       price: undefined
    #     }
    #   ]
    # },
    #
    def put(self, request, format=None):
        print(request.data)
        data = request.data
        jancode = data['jancode']
        inventory = data['inventory']

        with transaction.atomic():
            createtime = arrow.now()
            # create purchaseorder
            supplierObj = Supplier.objects.get(id=data['supplier'])
            inventoryObj = Inventory.objects.get(id=inventory)
            poObj = PurchaseOrder(
                orderid=data['orderid'],
                supplier=supplierObj,
                inventory=inventoryObj,
                create_time=createtime,
                status='在途', )
            poObj.save()

            for i in data['items']:
                # add purchase item
                poitemObj = PurchaseOrderItem(
                    jancode=Product.objects.get(jancode=jancode),
                    quantity=i['quantity'],
                    purchaseorder=poObj,
                    price=i['price'])
                poitemObj.save()

                # set inflight in stock
                stockObj = Stock.objects.get(
                    inventory=inventory, jancode=jancode)
                stockObj.inflight = F('inflight') + int(i['quantity'])
                stockObj.save()

                # update order, notes: may qty != quantity,
                orders = Order.objects.filter(
                    inventory=inventory, jancode=jancode, status='待采购')
                for o in orders:
                    o.purchaseorder = poObj
                    o.status = '已采购'
                    o.save(update_fields=['status', 'purchaseorder'])

            return Response(status=status.HTTP_201_CREATED)

        return Response(status=status.HTTP_400_BAD_REQUEST)


# 删除采购单
class PurchaseOrderDelete(views.APIView):
    # TODO: 增加是否需要重新采购的选项给用户
    #
    # 流程:
    #   1. 标记采购单状态: 删除.
    #   2. 取消关联订单的采购信息, 并重新标识订单状态为待采购.
    #   3. 修改关联库存记录, 减少在途库存.
    #
    #   request param: id
    def put(self, request, format=None):
        print(request.data)
        id = request.data.get('id')
        poObj = PurchaseOrder.objects.get(id=id)  # 采购单
        poitemObjs = poObj.purchaseorderitem.all()  # 关联采购商品
        orderObjs = poObj.order.all()  # 关联订单

        with transaction.atomic():

            # rollback order, set order status
            for o in orderObjs:
                if '已采购' in o.status:
                    o.status = '待采购'
                o.purchaseorder = None  # clear relate po
                o.save(update_fields=['status', 'purchaseorder'])

            # rollback stock, set stock preallocation
            for poi in poitemObjs:
                stockObj = Stock.objects.get(
                    jancode=poi.jancode, inventory=poObj.inventory)
                stockObj.preallocation = F('preallocation') - poi.quantity
                stockObj.save()

            # mark purchaseorder status as '删除'
            poObj.status = '删除'
            poObj.save(update_fields=['status'])
            return Response(status=status.HTTP_201_CREATED)

        return Response(status=status.HTTP_400_BAD_REQUEST)


# 清采购单(采购单入库)
class PurchaseOrderClear(views.APIView):
    # 流程:
    #   1. 标记采购单状态: 已入库.
    #   2. stock入库.
    #   3. 标记订单待发货.
    def put(self, request, format=None):
        print(request.data)
        id = request.data.get('id')
        inventory_id = request.data.get('inventory')
        pois = request.data.get('pois')
        poObj = PurchaseOrder.objects.get(id=id)  # 采购单

        with transaction.atomic():
            # mark purchaseorder
            poObj.status = '入库'
            poObj.save(update_fields=['status'])

            # stock in
            for poi in pois:
                inventory = Inventory.objects.get(id=inventory_id)
                stockObj = Stock.objects.get(
                    jancode=poi['jancode'], inventory=inventory)
                # 如果实际到库数量大于采购单记录, 入库实际到库数量,
                # 否则, 入库采购单记录数量, 并且需要处理漏采(漏采需补采购)
                if poi['quantity'] < poi['qty']:
                    stockObj.quantity = F('quantity') + poi['qty']
                else:
                    stockObj.quantity = F('quantity') + poi['quantity']
                stockObj.inflight = F('inflight') - poi['quantity']
                stockObj.save()

            # mark order
            # orderObjs = poObj.order.all()  # 关联订单
            # for o in orderObjs:
            #     if '已采购' in o.status:
            #         o.status = '待发货'
            #         o.save()
            poObj.order.filter(status='已采购').update(status='待发货')

            return Response(status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)


# 采购标记订单疑难
class OrderMarkConflict(views.APIView):
    # TODO: 分页
    #
    # 流程:
    #   1. 修改订单状态为: 需介入.
    #   2. 标记订单状态conflict字段
    #
    def put(self, request, format=None):
        print(request.data)
        data = request.data

        with transaction.atomic():
            for i in data:
                # mark conflict
                shipping = Shipping.objects.get(id=i['shipping'])
                inventory = Inventory.objects.get(id=i['inventory'])
                i.pop('shipping_name')
                i.pop('inventory_name')
                i['status'] = '需介入'
                i['shipping'] = shipping
                i['inventory'] = inventory
                i['purchaseorder'] = None
                s = Order(**i)
                s.save()
            return Response(status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)


# 需介入处理(协调退换货)
# 退款: 设置订单状态:已删除, 释放占用的库存. 换货: 释放占用的库存, 重新占用新库存.
# 注意: 换货意味着重新派单, 需要设置派单时间
class OrderConflict(views.APIView):
    def put(self, request, format=None):
        print(request.data)
        data = request.data

        with transaction.atomic():
            if '已删除' in data['status']:  # 退款
                stockObj = Stock.objects.get(
                    inventory=data['inventory'], jancode=data['jancode'])
                stockObj.preallocation = F(
                    'preallocation') - data['need_purchase']
                stockObj.save()
                orderObj = Order.objects.get(id=data['id'])
                orderObj.status = '已删除'
                orderObj.save(update_fields=['status'])
            else:  # 更换
                orderObj = Order.objects.get(id=data['id'])
                if orderObj.jancode != data['jancode']:
                    # 回滚旧的jancode库存占用
                    rollbackStockObj = Stock.objects.get(
                        inventory=orderObj.inventory, jancode=orderObj.jancode)
                    rollbackStockObj.preallocation = F(
                        'preallocation') - data['need_purchase']
                    rollbackStockObj.save()

                    # 判断新jancode库存是否满足
                    stockObj = Stock.objects.get(
                        inventory=data['inventory'], jancode=data['jancode'])
                    real_stock_qty = stockObj.quantity + stockObj.inflight - stockObj.preallocation
                    if data['quantity'] <= real_stock_qty:  # 库存足够, 记得取消采购标记(need_purchase=0)
                        stockObj.preallocation = F(
                            'preallocation') + data['quantity']
                        orderObj.status = '待发货'
                        orderObj.need_purchase = 0
                        orderObj.jancode = data['jancode']
                    else:
                        need_purchase = (
                            data['quantity'] - real_stock_qty
                        ) if real_stock_qty > 0 else data['quantity']
                        orderObj.need_purchase = need_purchase
                        orderObj.jancode = data['jancode']
                        orderObj.status = '待采购'
                        stockObj.preallocation = F(
                            'preallocation') + need_purchase
                    orderObj.allocate_time = arrow.now().format(
                        'YYYY-MM-DD HH:mm:ss')  # 需要更新订单分配时间
                    orderObj.save()
                    stockObj.save()

            return Response(status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)


# 订单删除流程:
#   if status == '预分配' then mark status=已删除
#   elif status == '待发货'|'需介入'|'已采购'|'待采购' then
#       mark order status = 已删除
#       rollback stock
#   else then
#       return error
#
class OrderDelete(views.APIView):
    def put(self, request, format=None):
        print(request.data)
        data = request.data

        orderObj = Order.objects.get(id=data['id'])
        with transaction.atomic():
            if '待处理' in orderObj.status:  # 直接标记删除
                orderObj.status = '已删除'
                orderObj.conflict_feedback = data['conflict_feedback']
                orderObj.save()
            elif ('待发货' in orderObj.status or '需介入' in orderObj.status or
                  '已采购' in orderObj.status or
                  '待采购' in orderObj.status):  # 清除占用的库存
                if orderObj.need_purchase:
                    stockObj = Stock.objects.get(
                        inventory=orderObj.inventory, jancode=orderObj.jancode)
                    stockObj.preallocation = F(
                        'preallocation') - orderObj.need_purchase
                    stockObj.save()
                orderObj.status = '已删除'
                orderObj.conflict_feedback = data['conflict_feedback']
                orderObj.save()
            elif '已删除' in orderObj.status:
                pass
            else:  # 不可删除, 已经分配DB单号, 需要先删除DB单号, 或者已经发货, 无法删除
                return Response(status=status.HTTP_406_NOT_ACCEPTABLE)

            return Response(status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)


# 采购单入库: 需要考虑对应订单被删除的情况


class UserInfo(generics.ListAPIView):
    queryset = Token.objects.all()
    serializer_class = TokenSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend, )
    filter_fields = ('key', )


class PurchaseOrderList(generics.ListCreateAPIView):

    # def get_queryset(self):
    #     queryset = PurchaseOrder.objects.all()
    #     workspace = self.request.query_params.get('workspace')
    #     airline = self.request.query_params.get('airline')

    #     if workspace:
    #         queryset = queryset.filter(workspace_id=workspace)
    #     elif airline:
    #         queryset = queryset.filter(workspace__airline_id=airline)

    #     return queryset

    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend, )
    filter_fields = ('orderid', 'inventory', 'supplier', 'status')


class PurchaseOrderDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer


class PurchaseOrderItemList(generics.ListCreateAPIView):

    queryset = PurchaseOrderItem.objects.all()
    serializer_class = PurchaseOrderItemSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend, )
    filter_fields = ('purchaseorder', )


class PurchaseOrderItemDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = PurchaseOrderItem.objects.all()
    serializer_class = PurchaseOrderItemSerializer


class ProductList(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend, )
    filter_fields = ('jancode', 'category', 'brand')


class ProductDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class OrderList(generics.ListCreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend, )
    filter_class = OrderFilter
    # filter_fields = ('orderid', 'channel_name', 'receiver_name', 'jancode',
    #                  'status')


class OrderDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer


class StockList(generics.ListCreateAPIView):
    queryset = Stock.objects.all()
    serializer_class = StockSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend, )
    filter_fields = ('jancode', 'inventory')


class StockDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Stock.objects.all()
    serializer_class = StockSerializer


class ShippingList(generics.ListCreateAPIView):
    queryset = Shipping.objects.all()
    serializer_class = ShippingSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend, )
    filter_fields = ('inventory', )


class ShippingDBList(generics.ListAPIView):
    queryset = ShippingDB.objects.all()
    serializer_class = ShippingDBSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend, )
    filter_fields = ('inventory', 'status')


class InventoryList(generics.ListCreateAPIView):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend, )


class SupplierList(generics.ListCreateAPIView):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend, )
