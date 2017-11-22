import asyncio
import json
import logging

import aiohttp
import arrow.arrow
from django.db import IntegrityError, transaction
from django.db.models import F
from rest_framework import status, views
from rest_framework.response import Response

from stock.models import (Inventory, Order, Product, PurchaseOrderItem,
                          Shipping, ShippingDB, Stock, StockOutRecord,
                          StockInRecord)
from ymatou import uex, utils

uex_user = '2830020@qq.com'
uex_passwd = '20162017'

# debug
# access_token = 'ACiYUZ6aKC48faYFD6MpvbOf73BdE9OV5g15q1A6Ghs+i/XIawq/9RHJCzc6Y3UNxA=='
# client_secret = 'APvYM8Mt5Xg1QYvker67VplTPQRx28Qt/XPdY9D7TUhaO3vgFWQ71CRZ/sLZYrn97w=='.lower(
# )
# client_id = '68993573-E38D-4A8A-A263-055C401F9369'

logger = logging.getLogger(__name__)


class SyncStock(views.APIView):
    def post(self, request, format=None):
        data = request.data
        impInventory = data['inventory_name']
        inv_dict = {
            '贝海': ['virtualstock-products', 'stock'],
            '广州': [u'国内库存出入库流水.xls', u'库存表'],
            '东京': ['tokyo_stock.xlsx', 'new'],
        }
        gsp = inv_dict[impInventory][0]
        wks = inv_dict[impInventory][1]
        inventoryObj = Inventory.objects.get(name=impInventory)
        syncer = utils.GoogleSpread()
        syncer.open_google_doc(gsp)
        stocks = syncer.read_google_doc_by_range(wks, 'A2:C', all_rows=True)
        with transaction.atomic():
            for i in list(syncer.chunks(stocks, 3)):
                if not i[2]:
                    continue
                productObj = None
                try:
                    productObj = Product.objects.get(jancode=i[0])
                except Product.DoesNotExist:
                    logger.info('Sync stock error, Jancode %s', i[0])
                    continue
                try:
                    stockObj = Stock.objects.get(
                        product=productObj, inventory=inventoryObj)
                    oldQuantity = stockObj.quantity
                    # if '东京' in impInventory:
                    #     stockObj.quantity = F('quantity') + i[2]
                    # else:
                    #     stockObj.quantity = i[2]
                    stockObj.quantity = i[2]
                    stockObj.save(update_fields=['quantity'])
                    stockObj.refresh_from_db()
                    incr = stockObj.quantity - oldQuantity
                    if incr > 0:  # 检查是否有待采购, 如果有待采购, 标记成待发货
                        ords = Order.objects.filter(
                            jancode=i[0], inventory=inventoryObj, status='待采购')
                        if ords:
                            for od in ords:
                                if od.need_purchase > incr:
                                    od.need_purchase = F('need_purchase') - incr
                                    od.save()
                                    break
                                incr = incr - od.need_purchase
                                od.need_purchase = None
                                if not od.shippingdb:
                                    od.status = '需面单'
                                else:
                                    od.status = '待发货'
                                od.save()
                                if incr == 0: break

                except Stock.DoesNotExist:
                    stockObj = Stock(
                        product=productObj,
                        quantity=i[2],
                        inventory=inventoryObj,
                        preallocation=0,
                        inflight=0,
                    )
                    stockObj.save()
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)


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
        logger.debug('UexStockOut: %s', result)
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
                    product__jancode=orderObj.jancode,
                    inventory=orderObj.inventory)
                stockObj.quantity = F('quantity') - orderObj.quantity  # 扣减库存
                stockObj.preallocation = F('preallocation') - orderObj.quantity
                stockObj.save()
        return Response(data=result, status=status.HTTP_200_OK)


# 订单发货
class StockOut(views.APIView):
    # 1. 标记db面单状态, 设置运单号(delivery_no);
    # 2. 标记订单状态, 过滤条件是订单状态: ('待发货')
    # 3. 扣减库存, 并记录出库stockoutrecord
    def post(self, request, format=None):
        delivery_no = request.data['delivery_no']
        dbs = request.data['db_numbers'].split('\n')
        logger.debug('出库调试, 用户输入:%s', dbs)
        results = None
        try:
            with transaction.atomic():
                for db in dbs:
                    try:
                        shippingdbObj = ShippingDB.objects.get(db_number=db)
                        if '已出库' in shippingdbObj.status:
                            results = {
                                'errmsg':
                                '面单:{} 已出库, 运单号:{}, 请确认订单是否已发货'.format(
                                    db, shippingdbObj.delivery_no)
                            }
                            if shippingdbObj.delivery_no == delivery_no:
                                results = {
                                    'errmsg': '面单:{} 重复录入或重复打包, 请检查'.format(db)
                                }
                            logger.debug('出库调试-异常, Errmsg: %s',
                                         results['errmsg'])
                            raise IntegrityError
                    except ShippingDB.DoesNotExist:
                        results = {'errmsg': '面单:{} 不存在, 请检查录入面单号'.format(db)}
                        logger.debug('出库调试-异常, Errmsg: %s', results['errmsg'])
                        raise IntegrityError
                    shippingdbObj.status = '已出库'
                    shippingdbObj.delivery_no = delivery_no
                    shippingdbObj.delivery_time = arrow.now().format(
                        'YYYY-MM-DD HH:mm:ss')
                    shippingdbObj.save(update_fields=[
                        'status', 'delivery_no', 'delivery_time'
                    ])
                    for o in shippingdbObj.order.filter(
                            status__in=['待发货', '已采购']):
                        if '已采购' in o.status:
                            results = {
                                'errmsg':
                                '面单{}对应的订单:{}, 采购在途, 采购单号:{}, 请确认'.format(
                                    db, o.orderid, o.purchaseorder.orderid)
                            }
                            logger.debug('出库调试-异常-2, Errmsg: %s',
                                         results['errmsg'])
                            raise IntegrityError
                        o.status = '已发货'
                        o.save(update_fields=['status'])
                        stockObj = Stock.objects.get(
                            product__jancode=o.jancode, inventory=o.inventory)
                        stockObj.quantity = F('quantity') - o.quantity
                        stockObj.preallocation = F('preallocation') - o.quantity
                        stockObj.save()
                        stockORObj = StockOutRecord(
                            orderid=o.orderid,
                            quantity=o.quantity,
                            inventory=o.inventory,
                            product=stockObj.product,
                            out_date=shippingdbObj.delivery_time,
                        )
                        stockORObj.save()
        except IntegrityError:
            return Response(data=results, status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_200_OK)


# 拼邮订单和第三方保税订单出库操作
# 更新订单状态, 扣减库存
class OrderOut(views.APIView):
    # 修改库存状态, 记录stockoutrecord, 更新订单状态
    def post(self, request, format=None):
        ord = request.data
        with transaction.atomic():
            ordObj = Order.objects.get(id=ord['id'])
            if '已发货' not in ordObj.status:
                ordObj.status = '已发货'
                ordObj.domestic_delivery_no = ord['domestic_delivery_no']
                ordObj.domestic_delivery_company = ord[
                    'domestic_delivery_company']
                ordObj.save(update_fields=[
                    'status', 'domestic_delivery_no',
                    'domestic_delivery_company'
                ])
                productObj = Product.objects.get(jancode=ordObj.jancode)
                stockObj = Stock.objects.get(
                    product=productObj, inventory=ordObj.inventory)
                stockObj.preallocation = F('preallocation') - ordObj.quantity
                stockObj.quantity = F('quantity') - ordObj.quantity
                stockObj.save()
                stockORObj = StockOutRecord(
                    orderid=ordObj.orderid,
                    quantity=ordObj.quantity,
                    inventory=ordObj.inventory,
                    product=stockObj.product,
                    out_date=arrow.now().format('YYYY-MM-DD HH:mm:ss'),
                )
                stockORObj.save()
                return Response(status=status.HTTP_200_OK)
            else:
                results = {'errmsg': '订单已发货'}
                return Response(
                    data=results, status=status.HTTP_400_BAD_REQUEST)


# 采购到国内仓库的采购单入库
class DomesticStockIn(views.APIView):
    # 1. 标记采购单和采购明细状态
    # 2. 修改stock库存, 并且记录stockinrecord
    # 3. 如果从东京仓采购, 需要对东京仓做出库处理, 并且记录stockoutrecord(注意, 是采购单出库)
    # 4. 标记关联订单状态
    def post(self, request, format=None):
        data = request.data
        with transaction.atomic():
            poiObj = PurchaseOrderItem.objects.get(id=data['id'])
            poObj = poiObj.purchaseorder
            if '转运中' in poiObj.status:
                poiObj.status = '已入库'
                poiObj.stockin_date = arrow.now().format('YYYY-MM-DD HH:mm:ss')
                poiObj.save()
                inventory = poObj.inventory
                stockObj = Stock.objects.get(
                    product=poiObj.product, inventory=inventory)
                stockObj.quantity = F('quantity') + poiObj.quantity
                stockObj.inflight = F('inflight') - poiObj.quantity
                stockObj.save()
                stockIRObj = StockInRecord(
                    orderid=poObj.orderid,
                    inventory=poObj.inventory,
                    quantity=poiObj.quantity,
                    in_date=poiObj.stockin_date,
                    product=poiObj.product,
                )
                stockIRObj.save()

                # tokyo stock out if supplier is tokyo
                if '东京仓' in poObj.supplier.name:
                    stockTokyo = Stock.objects.get(
                        inventory=Inventory.objects.get(name='东京'),
                        product=poiObj.product,
                    )
                    stockTokyo.preallocation = F(
                        'preallocation') - poiObj.quantity
                    stockTokyo.quantity = F('quantity') - poiObj.quantity
                    stockTokyo.save()
                    # 记录出库到stockoutrecord表, 这里的orderid用采购单id
                    stockORObj = StockOutRecord(
                        orderid=poObj.orderid,
                        quantity=poiObj.quantity,
                        inventory=stockTokyo.inventory,
                        product=poiObj.product,
                        out_date=poiObj.stockin_date,
                    )
                    stockORObj.save()

                poObj.order.filter(
                    jancode=poiObj.product.jancode,
                    status='已采购',
                    shippingdb__isnull=False).update(status='待发货')
                poObj.order.filter(
                    jancode=poiObj.product.jancode,
                    status='已采购',
                    shippingdb__isnull=True).update(status='需面单')

            count = poObj.purchaseorderitem.filter(status='已入库').count()
            total = poObj.purchaseorderitem.all().count()
            # if count > 0:
            #     if count != total:
            #         poObj.status = '部分入库'
            #     else:
            #         poObj.status = '入库'
            #     poObj.save(update_fields=[
            #         'status',
            #     ])
            if count == total:
                poObj.status = '已入库'
                poObj.save(update_fields=[
                    'status',
                ])
            return Response(status=status.HTTP_200_OK)


# 清采购单(采购单入库)
class PurchaseOrderClear(views.APIView):
    # 流程:
    #   1. 标记采购单状态: 已入库.
    #   2. stock入库(减inflight, 增加quantity).
    #   3. 标记订单待发货.
    # 需要支持部分入库
    # 采购流程中, 国内采购需要增加转运, 流程如下:
    #   1. 采购商品到达东京, 东京仓库入库, 这个入库只是标记purchaseorderitem状态为"东京仓", 不做其他操作
    #   2. 增加页面, 显示所有状态为东京仓的purchaseorderitem, 东京仓库根据这个页面转运商品, 关联转运单号
    #   3. 广州仓人员收到转运包括, 做入库操作
    def put(self, request, format=None):
        id = request.data.get('id')
        inventory_id = request.data.get('inventory')
        pois = request.data.get('pois')
        logger.debug('PurchaseOrderClear入库调试: 用户输入 - {}'.format(request.data))
        poObj = PurchaseOrder.objects.get(id=id)  # 采购单

        with transaction.atomic():
            # mark purchaseorder
            # poObj.status = '入库'
            # poObj.save(update_fields=['status'])

            # stock in
            for poi in pois:
                poiObj = poObj.purchaseorderitem.get(
                    product__jancode=poi['jancode'])
                if not poi['qty'] or '已入库' == poiObj.status:
                    continue

                if inventory_id == 3:  # 如果是广州仓库, 只标记订单明细状态, 和采购单状态(入库中/转运中)
                    if poiObj.status in ['东京仓', '转运中']:
                        continue
                    poiObj.status = '东京仓'
                    poiObj.save()
                    continue

                poiObj.status = '已入库'
                poiObj.stockin_date = arrow.now().format('YYYY-MM-DD HH:mm:ss')
                poiObj.save()

                inventory = Inventory.objects.get(id=inventory_id)
                stockObj = Stock.objects.get(
                    product__jancode=poi['jancode'], inventory=inventory)
                # poi.quantity记录的是采购数量, qty是实际到库数量.
                # 入库实际到库数量, 扣减inflight数量用采购数量.
                # TODO: 如果实际到库少于采购数量, 需要处理漏采(漏采需补采购)
                cp = 0
                if poiObj.quantity < poi['qty']:
                    cp = poi['qty']
                else:
                    cp = poiObj.quantity
                stockObj.quantity = F('quantity') + cp
                stockObj.inflight = F('inflight') - poiObj.quantity
                stockObj.save()
                # 记录入库操作stockinrecord(采购单入库)
                stockIRObj = StockInRecord(
                    orderid=poObj.orderid,
                    inventory=poObj.inventory,
                    quantity=cp,
                    in_date=poiObj.stockin_date,
                    product=poiObj.product,
                )
                stockIRObj.save()

                # tokyo stock out if supplier is tokyo
                if '东京仓' in poObj.supplier.name:
                    stockTokyo = Stock.objects.get(
                        inventory=Inventory.objects.get(name='东京'),
                        product__jancode=poi['jancode'],
                    )
                    stockTokyo.preallocation = F(
                        'preallocation') - poiObj.quantity
                    # if poiObj.quantity < poi['qty']:
                    #     stockTokyo.quantity = F('quantity') - poi['qty']
                    # else:
                    #     stockTokyo.quantity = F('quantity') - poiObj.quantity
                    stockTokyo.quantity = F('quantity') - cp
                    stockTokyo.save()
                    # 记录出库到stockoutrecord表, 这里的orderid用采购单id
                    stockORObj = StockOutRecord(
                        orderid=poObj.orderid,
                        quantity=cp,
                        inventory=stockTokyo.inventory,
                        product=poiObj.product,
                        out_date=poiObj.stockin_date,
                    )
                    stockORObj.save()

                # 如果订单没有面单, 进入需面单状态, 否则待发货状态
                poObj.order.filter(
                    status='已采购',
                    jancode=poi['jancode'],
                    shippingdb__isnull=False).update(status='待发货')
                poObj.order.filter(
                    status='已采购',
                    jancode=poi['jancode'],
                    shippingdb__isnull=True).update(status='需面单')

            count = poObj.purchaseorderitem.filter(
                status__in=['已入库', '东京仓', '转运中']).count()
            all = poObj.purchaseorderitem.count(
            )  # 不能和用户提交的采购明细条数比较, 用户可能在其他页面增加了采购明细, 却不刷新提交页面
            if count > 0:
                if count != all:
                    poObj.status = '入库中'
                else:
                    poObj.status = '转运中' if inventory_id == 3 else '已入库'

                poObj.save(update_fields=[
                    'status',
                ])
            return Response(status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)
