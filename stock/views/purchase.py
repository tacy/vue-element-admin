import logging

import arrow.arrow
from django.db import IntegrityError, connection, transaction
from rest_framework import status, views
from rest_framework.response import Response
from django.db.models import F, Sum
from stock.exceptions import InputError
from stock.models import (Inventory, Order, Product, PurchaseOrder,
                          PurchaseOrderItem, Stock, Supplier)

from .order import computeOrderStatus
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


def createPO(orderid, inventory, supplier, items, createtime):
    # 如果在一个采购单里面, 重复录入一个商品, 会抛一致性异常
    supplierObj = Supplier.objects.get(id=supplier)
    inventoryObj = Inventory.objects.get(id=inventory)

    try:
        poObj = PurchaseOrder.objects.get(
            orderid=orderid, supplier=supplierObj, inventory=inventoryObj)
        if '在途中' not in poObj.status:
            return {
                'errtype': 'InputError',
                'errmsg': '注文编号{}已经存在, 且状态非在途. 请更换注文编号'.format(orderid),
            }
    except PurchaseOrder.DoesNotExist:
        poObj = PurchaseOrder(
            orderid=orderid,
            supplier=supplierObj,
            inventory=inventoryObj,
            create_time=createtime,
            status='在途中',
        )
        poObj.save()

    for i in items:
        # add purchase item
        if i['quantity'] < 1:
            return {
                'errtype': 'InputError',
                'errmsg': '商品{}采购数量必须大于1)'.format(i['jancode'])
            }
        try:
            productObj = Product.objects.get(jancode=i['jancode'])
        except Product.DoesNotExist:
            return {
                'errtype': 'InputError',
                'errmsg': '商品库中无该商品%s, 请先创建产品资料' % (i['jancode'], )
            }

        # 下面这段代码不需要, 直接抛出异常, 让用户知道
        # if poObj.purchaseorderitem.filter(
        #         product=Product.objects.get(jancode=i['jancode'])).count():
        #     logger.warning(
        #         'createPurchaseOrder: [%s], jancode:[%s]重复保存, 数量: %s',
        #         orderid,
        #         i['jancode'],
        #         i['quantity'],
        #     )
        #     continue  # 之前已经保存过了

        poitemObj = PurchaseOrderItem(
            product=productObj,
            quantity=i['quantity'],
            purchaseorder=poObj,
            status='在途中',
            price=i['price'])
        poitemObj.save()

        try:
            stockObj = Stock.objects.get(
                inventory=inventoryObj, product__jancode=i['jancode'])
            stockObj.inflight = F('inflight') + int(i['quantity'])
        except Stock.DoesNotExist:  # 如果第一次分配到该仓库, 主动在该仓库新建产品记录
            stockObj = Stock(
                product=productObj,
                inventory=inventoryObj,
                quantity=0,
                inflight=int(i['quantity']),
                preallocation=0)
        stockObj.save()

        # preallocation stock if supplier is tokyo
        if '东京仓' in supplierObj.name:
            try:
                stockTokyo = Stock.objects.get(
                    inventory=Inventory.objects.get(name='东京'),
                    product__jancode=i['jancode'],
                )
                stockTokyo.preallocation = F('preallocation') + int(
                    i['quantity'])
            except Stock.DoesNotExist:
                stockTokyo = Stock(
                    product=productObj,
                    inventory=Inventory.objects.get(name='东京'),
                    quantity=i['quantity'],
                    inflight=0,
                    preallocation=i['quantity'])
            stockTokyo.save()

        orders = Order.objects.filter(
            inventory__id=inventory, jancode=i['jancode'],
            status='待采购').order_by('id')
        c = int(i['quantity'])
        for o in orders:
            if o.need_purchase > c:
                break
            o.purchaseorder = poObj
            o.status = '已采购'
            o.save(update_fields=['status', 'purchaseorder'])
            c = c - o.need_purchase
    return None


# 生成采购单
class OrderPurchase(views.APIView):
    # TODO: 分页 / 限制只能多采不能少采
    #
    # 流程:
    #   1. 根据注文编号(purchaseorderid)生成purchaseorder.
    #   2. 同时生成purchaseitem.
    #   3. 标记关联订单状态:已采购, 并标注关联purchaseorder. (这里需要考虑采购和派单同时进行情况, 关联订单时需要比较时间[这个废弃, 直接按照订单id先后, 去关联订单])
    #   4. 修改关联库存记录, 增加在途库存.
    #   5. 采购渠道是东京, 占用库存
    #
    def put(self, request, format=None):
        data = request.data.get('data')
        # queryTime = request.data.get('queryTime')
        inventory = request.data.get('inventory')
        results = {}
        try:
            with transaction.atomic():
                createtime = arrow.now()
                pos = {}
                # 转换输入参数成{'orderid': {'supplier':, 'inventory':, 'items':[{'jancode':,'quantity':,'price':}]},}
                for i in data:
                    # create purchaseorder
                    po_id = i.get('purchaseorderid')
                    if not po_id:
                        continue
                    if not i['quantity'] or i['quantity'] < i['qty'] or not i['supplier'] or not i['price'] or (
                            inventory == 3 and i['supplier'] == '东京仓'
                            and i['quantity'] > i['tokyo_stock']) or (
                                po_id in pos
                                and pos[po_id]['supplier'] != i['supplier']):
                        results = {
                            'errmsg':
                            '请检查商品{}输入. (注意, 从东京仓采购, 采购数量不能超过库存)'.format(
                                i['jancode'])
                        }
                        raise InputError(None, None)
                    item = {
                        'jancode': i['jancode'],
                        'quantity': i['quantity'],
                        'price': i['price'],
                    }
                    if po_id in pos:
                        pos[po_id]['items'].append(item)
                    else:
                        pos[po_id] = {
                            'inventory': inventory,
                            'supplier': i['supplier'],
                            'items': [
                                item,
                            ]
                        }
                for k, v in pos.items():
                    results = createPO(
                        k,
                        v['inventory'],
                        v['supplier'],
                        v['items'],
                        createtime,
                    )
                    if results:
                        raise InputError
        except (IntegrityError, InputError) as e:
            logger.exception('保存采购单异常')
            if e.args and e.args[0] == 1062:
                return Response(
                    data={'errmsg': '同一产品需合并录入'},
                    status=status.HTTP_400_BAD_REQUEST)
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
    #   payment: ,
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
        supplier = data['supplier']
        results = {}
        if Supplier.objects.get(id=supplier).name == '东京仓':
            for i in data['items']:
                try:
                    stockObj = Stock.objects.get(
                        product__jancode=i['jancode'],
                        inventory=Inventory.objects.get(name='东京'))
                    realstock = stockObj.quantity + stockObj.inflight - stockObj.preallocation
                    if i['quantity'] > realstock:
                        return Response(
                            data={
                                'errmsg':
                                '产品[%s]采购数量超出东京仓库存数量' % (i['jancode'])
                            },
                            status=status.HTTP_400_BAD_REQUEST)
                except Stock.DoesNotExist:
                    return Response(
                        data={'errmsg': '产品[%s]在东京仓没有入库记录' % (i['jancode'])},
                        status=status.HTTP_400_BAD_REQUEST)
        try:
            with transaction.atomic():
                createtime = arrow.now()
                # create purchaseorder

                results = createPO(
                    data['orderid'],
                    inventory,
                    supplier,
                    data['items'],
                    createtime,
                )
                if results:
                    raise InputError(None, None)
        except (IntegrityError, InputError) as e:
            if e.args and e.args[0] == 1062:
                return Response(
                    data={'errmsg': '同一产品需合并录入'},
                    status=status.HTTP_400_BAD_REQUEST)
            return Response(data=results, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_201_CREATED)


# 删除采购单
class PurchaseOrderDelete(views.APIView):
    # TODO: 增加是否需要重新采购的选项给用户
    #
    # 流程:
    #   1. 标记采购单状态: 删除.
    #   2. 修改关联库存记录, 回滚在途库存.
    #   3. 修改订单状态
    #      a. 需要走类似派单判断订单状态流程, 如果现有库存不满足, 置为需采购
    #         记得需要计算need_purchase
    #      b. 如果库存满足, 需要判断是否是在途库存满足还是在库库存满足(quantity)
    #         如果在库库存满足, 直接标记订单需面单或待发货(看看是否有面单)
    #         如果在途库存满足, 关联采购单, 标记订单状态已采购
    #
    #   request param: id
    def put(self, request, format=None):
        id = request.data.get('id')
        poObj = PurchaseOrder.objects.get(id=id)  # 采购单
        poitemObjs = poObj.purchaseorderitem.all()  # 关联采购商品
        # orderObjs = poObj.order.filter(status='已采购')  # 关联订单, 状态为已采购

        with transaction.atomic():
            # rollback stock, set stock preallocation
            for poi in poitemObjs:
                # 回滚在途
                stockObj = Stock.objects.get(
                    product=poi.product, inventory=poObj.inventory)
                stockObj.inflight = F('inflight') - poi.quantity
                stockObj.save(update_fields=['inflight'])
                stockObj.refresh_from_db()

                # rollback tokyo stock if supplier is tokyo
                if '东京仓' in poObj.supplier.name:
                    stockTokyo = Stock.objects.get(
                        inventory=Inventory.objects.get(name='东京'),
                        product=poi.product,
                    )
                    stockTokyo.preallocation = F('preallocation') - poi.quantity
                    stockTokyo.save()

                # 判断是否关联订单, 如果有关联订单, 需要回滚, 如果没有, 跳过处理
                ordObjs = Order.objects.filter(
                    purchaseorder__id=id,
                    jancode=poi.product.jancode,
                    status='已采购')
                totalQuantity = ordObjs.aggregate(
                    Sum('quantity'))['quantity__sum']
                if not totalQuantity:
                    continue
                stockPreallocation = stockObj.preallocation - totalQuantity  # 伪回滚占用
                stockQuantity = stockObj.quantity
                stockInflight = stockObj.inflight
                for o in ordObjs:
                    stockPreallocation += o.quantity
                    purchaseQuantity = stockPreallocation - (
                        stockQuantity + stockInflight)

                    (
                        o.status,
                        o.need_purchase,
                        o.purchaseorder,
                    ) = computeOrderStatus(
                        purchaseQuantity,
                        o,
                        stockPreallocation,
                        stockQuantity,
                    )
                    o.save()

            # mark purchaseorder status as '删除'
            poitemObjs.update(status='已删除')
            poObj.status = '已删除'
            poObj.save(update_fields=['status'])
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
