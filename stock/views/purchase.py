import logging

import arrow.arrow
from django.db import IntegrityError, connection, transaction
from rest_framework import status, views
from rest_framework.response import Response
from django.db.models import F
from stock.exceptions import InputError
from stock.models import (Inventory, Order, Product, PurchaseOrder,
                          PurchaseOrderItem, Stock, Supplier, StockInRecord,
                          StockOutRecord)

logger = logging.getLogger(__name__)


# 获取采购列表
class OrderPurchaseList(views.APIView):
    # TODO: 分页
    # 需要返回查询时间, 创建采购单的时候, 我们需要用这个时间来和订单的派单时间做对比, 看看是否能关联相关订单
    # 国内的拼邮单, 采购之前需要看看东京仓库是否有货.
    #
    def get(self, request, format=None):
        sql = "select p.jancode, p.name product_name, p.purchase_link1, p.purchase_link2, p.purchase_link3, p.specification sku_properties_name, min(piad_time) piad_time, max(o.price) product_price, sum(o.need_purchase) qty from stock_product p inner join stock_order o on o.jancode=p.jancode where o.status='待采购' and o.inventory_id=%s group by jancode order by o.id"
        sql2 = "select quantity+inflight-preallocation tokyo_stock from stock_stock where inventory_id='4' and product_id=(select id from stock_product where jancode=%s)"
        sql3 = "select jancode from stock_order where seller_name='天狗' and status='待采购' and jancode=%s"

        def dictfetchall(cursor):
            "Return all rows from a cursor as a dict"
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

        inventory = request.query_params.get('inventory')
        with connection.cursor() as c:
            c.execute(sql, [inventory])
            results = dictfetchall(c)
            for i, r in enumerate(results):
                c.execute(sql3, [r['jancode']])
                isTiangou = c.fetchall()
                results[i]['isTiangou'] = '是' if isTiangou else '否'
                if int(inventory) == 3:  # 需要查东京库存
                    c.execute(sql2, [r['jancode']])
                    rt = c.fetchone()
                    results[i]['tokyo_stock'] = rt[0] if rt else 0
                else:
                    results[i]['tokyo_stock'] = 0
            logger.debug('orderPurchaseList: %s', results)
            data = {
                'data': results,
                'queryTime': arrow.now().format('YYYY-MM-DD HH:mm:ss')
            }
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
    #   5. 采购渠道是东京, 占用库存
    #
    def put(self, request, format=None):
        data = request.data.get('data')
        queryTime = request.data.get('queryTime')
        inventory = request.data.get('inventory')
        results = {}
        try:
            with transaction.atomic():
                createtime = arrow.now()
                pos = {}
                for i in data:
                    # create purchaseorder
                    po_id = i.get('purchaseorderid')
                    if not po_id:
                        continue
                    if (not i['quantity'] or i['quantity'] < i['qty']
                            or not i['supplier'] or not i['price']):
                        results = {'errmsg': '请检查输入'}
                        raise InputError
                    jancode = i['jancode']
                    if po_id not in pos:
                        supplierOb = Supplier.objects.get(id=i['supplier'])
                        inventoryOb = Inventory.objects.get(id=inventory)
                        try:
                            po = PurchaseOrder.objects.get(
                                orderid=po_id, supplier=supplierOb)
                            if '在途' not in po.status:
                                results = {
                                    'errmsg': '注文编号已经存在, 且状态非在途. 请更换注文编号'
                                }
                                raise InputError
                        except PurchaseOrder.DoesNotExist:
                            po = PurchaseOrder(
                                orderid=po_id,
                                supplier=supplierOb,
                                inventory=inventoryOb,
                                create_time=createtime,
                                status='在途',
                            )
                            po.save()
                        pos[po_id] = po

                    # add purchase item
                    price = i['price']
                    if pos[po_id].purchaseorderitem.filter(
                            product=Product.objects.get(
                                jancode=jancode)).count():
                        continue  # 之前已经保存过了

                    poitem = PurchaseOrderItem(
                        product=Product.objects.get(jancode=jancode),
                        quantity=i['quantity'],
                        purchaseorder=pos[po_id],
                        price=price)
                    poitem.save()

                    # set inflight in stock
                    stock = Stock.objects.get(
                        inventory=inventory,
                        product__jancode=jancode,
                    )
                    stock.inflight = F('inflight') + int(i['quantity'])
                    stock.save()

                    # preallocation stock if supplier is tokyo
                    if '东京仓' in supplierOb.name:
                        stockTokyo = Stock.objects.get(
                            inventory=Inventory.objects.get(name='东京'),
                            product__jancode=jancode,
                        )
                        stockTokyo.preallocation = F('preallocation') + int(
                            i['quantity'])
                        stockTokyo.save()

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
        except (IntegrityError, InputError) as e:
            logger.exception('保存采购单异常')
            return Response(data=results, status=status.HTTP_400_BAD_REQUEST)

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
        data = request.data
        logger.debug('新建采购单调试:%s', data)
        inventory = data['inventory']
        results = {}
        try:
            with transaction.atomic():
                createtime = arrow.now()
                # create purchaseorder
                supplierObj = Supplier.objects.get(id=data['supplier'])
                inventoryObj = Inventory.objects.get(id=inventory)
                try:
                    poObj = PurchaseOrder.objects.get(
                        orderid=data['orderid'], supplier=supplierObj)
                    if '在途' not in poObj.status:
                        results = {'errmsg': '注文编号已经存在, 且状态非在途. 请更换注文编号'}
                        raise InputError
                except PurchaseOrder.DoesNotExist:
                    poObj = PurchaseOrder(
                        orderid=data['orderid'],
                        supplier=supplierObj,
                        inventory=inventoryObj,
                        create_time=createtime,
                        status='在途',
                    )
                    poObj.save()

                for i in data['items']:
                    # add purchase item
                    try:
                        productObj = Product.objects.get(jancode=i['jancode'])
                    except Product.DoesNotExist:
                        results = {
                            'errmsg': '商品库中无该商品%s, 请先创建产品资料' % (i['jancode'], )
                        }
                        raise IntegrityError
                    poitemObj = PurchaseOrderItem(
                        product=productObj,
                        quantity=i['quantity'],
                        purchaseorder=poObj,
                        price=i['price'])
                    poitemObj.save()

                    try:
                        stockObj = Stock.objects.get(
                            inventory=inventoryObj,
                            product__jancode=i['jancode'])
                    except Stock.DoesNotExist:  # 如果第一次分配到该仓库, 主动在该仓库新建产品记录
                        stockObj = Stock(
                            product=productObj,
                            inventory=inventoryObj,
                            quantity=0,
                            inflight=0,
                            preallocation=0)
                    stockObj.inflight = stockObj.inflight + int(i['quantity'])
                    stockObj.save()

                    # preallocation stock if supplier is tokyo
                    if '东京仓' in supplierObj.name:
                        stockTokyo = Stock.objects.get(
                            inventory=Inventory.objects.get(name='东京'),
                            product__jancode=i['jancode'],
                        )
                        stockTokyo.preallocation = F('preallocation') + int(
                            i['quantity'])
                        stockTokyo.save()

                    orders = Order.objects.filter(
                        inventory__id=inventory,
                        jancode=i['jancode'],
                        status='待采购').order_by('id')
                    c = int(i['quantity'])
                    for o in orders:
                        if o.need_purchase > c:
                            break
                        o.purchaseorder = poObj
                        o.status = '已采购'
                        o.save(update_fields=['status', 'purchaseorder'])
                        c = c - o.need_purchase
                return Response(status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            if e.args and e.args[0] == 1062:
                return Response(
                    data={'errmsg': '同一产品需合并录入'},
                    status=status.HTTP_400_BAD_REQUEST)
            return Response(data=results, status=status.HTTP_400_BAD_REQUEST)


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
        id = request.data.get('id')
        poObj = PurchaseOrder.objects.get(id=id)  # 采购单
        poitemObjs = poObj.purchaseorderitem.all()  # 关联采购商品
        orderObjs = poObj.order.filter(status='已采购')  # 关联订单, 状态为已采购

        with transaction.atomic():

            # rollback order, set order status
            for o in orderObjs:
                o.status = '待采购'
                o.purchaseorder = None  # clear relate po
                o.save(update_fields=['status', 'purchaseorder'])

            # rollback stock, set stock preallocation
            for poi in poitemObjs:
                stockObj = Stock.objects.get(
                    product=poi.product, inventory=poObj.inventory)
                stockObj.inflight = F('inflight') - poi.quantity
                stockObj.save(update_fields=[
                    'inflight',
                ])

                # rollback tokyo stock if supplier is tokyo
                if '东京仓' in poObj.supplier.name:
                    stockTokyo = Stock.objects.get(
                        inventory=Inventory.objects.get(name='东京'),
                        product=poi.product,
                    )
                    stockTokyo.preallocation = F('preallocation') - poi.quantity
                    stockTokyo.save()

            # mark purchaseorder status as '删除'
            poObj.status = '删除'
            poObj.save(update_fields=['status'])
            return Response(status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)


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

                if inventory_id == 3:  # 如果是广州仓库, 只标记订单明细状态
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

                poObj.order.filter(
                    status='已采购', jancode=poi['jancode']).update(status='待发货')

            count = poObj.purchaseorderitem.filter(status='已入库').count()
            all = poObj.purchaseorderitem.count(
            )  # 不能和用户提交的采购明细条数比较, 用户可能在其他页面增加了采购明细, 却不刷新提交页面
            if count > 0:
                if count != all:
                    poObj.status = '部分入库'
                else:
                    poObj.status = '入库'
                poObj.save(update_fields=[
                    'status',
                ])
            return Response(status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)


class PurchaseOrderTransform(views.APIView):
    # 标记purchaseorderitem状态, 记录转运单号
    def post(self, request, format=None):
        data = request.data
        logger.debug('purchaseOrderTransform debug: %s', data)
        with transaction.atomic():
            for i in data['purchaseorderitems']:
                poiObj = PurchaseOrderItem.objects.get(id=i['id'])
                poiObj.status = '转运中'
                poiObj.delivery_no = data['delivery_no']
                poiObj.save()
        return Response(status=status.HTTP_200_OK)
