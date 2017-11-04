import logging

import arrow.arrow
from django.db import IntegrityError, connection, transaction
from django.db.models import F, Max
from rest_framework import status, views
from rest_framework.response import Response

from stock.models import (Inventory, Order, Product, PurchaseOrder, Shipping,
                          Stock, UexTrack, ShippingDB)

logger = logging.getLogger(__name__)


# 拼邮订单和第三方保税订单出库操作
# 更新订单状态, 扣减库存
class OrderOut(views.APIView):
    def post(self, request, format=None):
        ord = request.data
        with transaction.atomic():
            ordObjs = Order.objects.get(id=ord['id'])
            if '已发货' not in ordObjs.status:
                ordObjs.status = '已发货'
                ordObjs.save(update_fields=['status'])
                productObj = Product.objects.get(jancode=ordObjs.jancode)
                stockObj = Stock.objects.get(
                    product=productObj, inventory=ordObjs.inventory)
                stockObj.preallocation = F('preallocation') - ordObjs.quantity
                stockObj.quantity = F('quantity') - ordObjs.quantity
                stockObj.save()
                return Response(status=status.HTTP_200_OK)
            else:
                results = {'errmsg': '订单已发货'}
                return Response(
                    data=results, status=status.HTTP_400_BAD_REQUEST)


# 不要使用, 有问题, stock没有jancode字段了
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
        with connection.cursor() as c:
            c.execute(sql, (db_number, ))
            results = dictfetchall(c)
            data = {
                'results': results,
            }
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
            return Response(data=data, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)


# 录入订单
class OrderTPRCreate(views.APIView):
    def put(self, request, format=None):
        data = request.data
        t = arrow.now()
        piad_time = t.format('YYYY-MM-DD HH:mm:ss')
        # orderid = 'T' + t.format('YYMMDD') + ''.join(
        #     random.choices(string.digits, k=2))
        with transaction.atomic():
            for p in data['products']:
                o = {
                    'orderid': data['orderid'],
                    'piad_time': piad_time,
                    'delivery_type': data['delivery_type'],
                    'seller_name': data['seller_name'],
                    'channel_name': data['channel_name'],
                    'receiver_name': data['receiver_name'],
                    'receiver_address': data['receiver_address'],
                    'receiver_zip': data.get('receiver_zip'),
                    'receiver_mobile': data['receiver_mobile'],
                    'receiver_idcard': data.get('receiver_idcard'),
                    'seller_memo': data.get('seller_memo'),
                    'jancode': p['jancode'],
                    'product_title': p['product_title'],
                    'sku_properties_name': p['sku_properties_name'],
                    'price': p['price'],
                    'payment': float(p['price']) * float(p['quantity']),
                    'quantity': p['quantity']
                }
                orderObj = Order(**o)
                orderObj.save()
        return Response(status=status.HTTP_200_OK)


# 订单预处理
class OrderAllocate(views.APIView):
    # 派单涉及到两个表: order和stock
    # 派单需要的操作: 1. 占用库存(preallocation); 2. 标记订单需要采购的数量(need_purchase);
    # 3. 修改订单状态(status:待发货/待采购)
    #
    # 派单流程: 派单分为派单和重派, 如果订单的inventory字段为空, 定位为派单;
    # 如果该字段非空, 定义为重派.
    #
    # 计算商品库存是否能满足订单发需求的时候, 需要特别注意, 如果在库实际不足, 但是在库+在途能满足,
    # 需要标记订单状态为已采购, 同时关联最晚采购该商品的采购订单
    #
    # 需要根据传入订单号, 查询数据库表中对应订单, 判断order_inventory字段内容:
    # if paramorder.status == '已删除'; then delete order opetion, use in conflict
    # if paramorder.inventory is null; then return
    # if dborder.inventory is null; then 派单
    #
    # 重派不考虑了, 已经支持弹回功能.
    # if dborder.inventory != paramorder.inventory; then 重派
    # if dborder.inventory == paramorder.inventory:
    #     if dborder.shipping == paramorder.shipping; then return
    #     if dborder.shipping != paramorder.shipping; then (仅仅更新order数据, 无需更新库存信息)
    #
    #
    # update order status
    # if stock(quantity+inflight-preallocation) > 0: 待发货 else 采购
    #
    # 派单需要更新库存占库字段; 重派需要先从之前指派的仓库回滚占库数据, 再更新库存占
    # 库字段;
    #
    # 支持购物车派单和批量派单
    #
    # 需要支持轨迹运输模式, 轨迹运输模式在派单的时候直接给订单分配轨迹单号(不管订单是否需要采购,
    # 主要是考虑到发货的时效性), 轨迹单(shippingdb)状态直接设置为已出库, 直接给国内处理, 不需要
    # 东京仓参与
    #
    def put(self, request, format=None):
        allocateData = request.data
        logger.debug('派单调试:%s', allocateData)
        allocate_time = arrow.now().format('YYYY-MM-DD HH:mm:ss')
        paramInventory = allocateData['inventory']
        relate_inventory = Inventory.objects.get(id=paramInventory)
        relate_shipping = Shipping.objects.get(id=allocateData['shipping'])
        # if not paramInventory or not paramShipping:  # 传入参数为空, 无效
        #     return status.HTTP_400_BAD_REQUEST

        orders = []
        if allocateData['id'] == 'batchallocate':  # batchAllocate
            allOrders = Order.objects.filter(
                jancode=allocateData['jancode'], status='待处理')
            for ao in allOrders:  # batch allocate ignore shipCart order
                # check if is shipcart order
                ordid_pre = ao.orderid.split('-')[0]
                c = Order.objects.filter(orderid__contains=ordid_pre).count()
                # print(ao, ordid_pre, c)
                if c == 1:
                    orders.append(ao)
        else:  # 单个订单派
            # check if is shipcart order
            ordid_pre = allocateData['orderid'].split('-')[0]
            orders = Order.objects.filter(
                orderid__contains=ordid_pre, status='待处理')

        # 检查是否订单商品已经在product表中, 如不存在, 返回错误提示
        jans = set([v.jancode for v in orders])
        prodObjs = {}
        for j in jans:
            try:
                productObj = Product.objects.get(jancode=j)
                prodObjs[j] = productObj
            except Product.DoesNotExist:
                results = {'errmsg': '商品库中无[{}], 请先创建产品资料'.format(j)}
                return Response(
                    data=results, status=status.HTTP_400_BAD_REQUEST)

        try:
            errmsg = {}
            with transaction.atomic():
                # 轨迹订单处理: 这里需要先判断是否特殊运输方式: 轨迹
                uex_number = None
                shippingdbObj = None
                if relate_shipping.name == '轨迹':
                    uextrackObj = UexTrack.objects.filter(
                        allocate_time__isnull=True)[0]
                    uex_number = uextrackObj.uex_number
                    uextrackObj.allocate_time = allocate_time
                    uextrackObj.save()
                    shippingdbObj = ShippingDB(
                        db_number=uex_number,
                        status='已出库',
                        channel_name=orders[0].channel_name,
                        order_piad_time=orders[0].piad_time,
                        shipping=relate_shipping,
                        inventory=relate_inventory)
                    shippingdbObj.save()

                for dborder in orders:
                    # 检查被指派的仓库, 是否该产品已经在仓库中存在, 如果不存在, 创建
                    try:
                        stockObj = Stock.objects.get(
                            inventory=paramInventory,
                            product=prodObjs[dborder.jancode])
                    except Stock.DoesNotExist:  # 如果第一次分配到该仓库, 主动在该仓库新建产品记录
                        stockObj = Stock(
                            product=prodObjs[dborder.jancode],
                            inventory=relate_inventory,
                            quantity=0,
                            inflight=0,
                            preallocation=0)
                        stockObj.save()
                    # dborder = Order.objects.get(id=orderInfo['id'])
                    dbinventory = dborder.inventory

                    # rollbackstock = ''
                    # 计算库存变化
                    if not dbinventory:  # 派单
                        stockObj.preallocation = F(
                            'preallocation') + dborder.quantity  # 分配订单需要占库存
                    # else:  # 重新派单
                    #     if dbinventory.id != paramInventory:  # 重派单, 订单派给了新的仓库, 需要回滚之前的库存占用
                    #         rollbackstock = Stock.objects.get(
                    #             inventory=dbinventory.id,
                    #             product__id=productObj.id)
                    #         rollbackstock.preallocation = F(
                    #             'preallocation') - dborder.quantity
                    #         stockObj.preallocation = F(
                    #             'preallocation') + dborder.quantity
                    #     else:  # 重派单, 但是仓库没有改变, 无需对库存做更新
                    #         if dborder.shipping.id == allocateData[
                    #                 'shipping']:  # 派单信息没有变化, 无需处理.
                    #             return Response(status=status.HTTP_200_OK)
                    #         dborder.shipping = Shipping.objects.get(
                    #             id=allocateData['shipping'])
                    #         dborder.save(update_fields=[
                    #             'shipping',
                    #         ])
                    #         return Response(status=status.HTTP_200_OK)
                    else:
                        errmsg = {
                            'errmsg':
                            '订单:[%s]状态异常, 请通知技术解决' % (dborder.orderid, ),
                        }
                        raise IntegrityError

                    # 计算订单状态
                    stockObj.save()
                    # 使用F操作models, save之后需要从数据库刷新, 否则值不能使用
                    stockObj.refresh_from_db()

                    dborder.allocate_time = allocate_time  # 如果更新库存表, 就需要更新派单时间
                    purchaseQuantity = stockObj.preallocation - (
                        stockObj.quantity + stockObj.inflight)
                    if purchaseQuantity > 0:  # 订单需采购
                        if purchaseQuantity < dborder.quantity:
                            dborder.need_purchase = purchaseQuantity
                        else:
                            dborder.need_purchase = dborder.quantity
                        dborder.status = '待采购'
                    else:
                        # 到这里, 虽然订单不需要采购, 但是如果在库不能满足发货需求, 该订单需要和
                        # 在途的采购单绑定, 同时标记状态为已采购
                        if stockObj.preallocation > stockObj.quantity:
                            dborder.status = '已采购'
                            # 找到最新的采购单
                            id = PurchaseOrder.objects.filter(
                                purchaseorderitem__product__jancode=dborder.
                                jancode,
                                # purchaseorderitem__status__isnull=True,    # 不知道为什么要判断
                                status__in=('在途', '部分入库')).aggregate(
                                    Max('id'))
                            dborder.purchaseorder = PurchaseOrder.objects.get(
                                id=id['id__max'])
                        else:
                            dborder.status = '待发货'

                    # 更新订单和仓库信息, 如果是轨迹订单, 需要特殊处理
                    dborder.shipping = Shipping.objects.get(
                        id=allocateData['shipping'])
                    dborder.inventory = relate_inventory

                    # 轨迹订单处理: 轨迹订单直接分配uex单号,不管是否需要采购
                    if uex_number:
                        dborder.shippingdb = shippingdbObj
                        dborder.export_status = '待导出'

                    dborder.save()

                    # if rollbackstock:
                    #     rollbackstock.save()
                return Response(status=status.HTTP_200_OK)
        except (IntegrityError, IndexError) as e:
            if type(e).__name__ == 'IndexError':
                errmsg = {'errmsg': 'Uex单号已经分配完成, 请增加Uex号段'}
            logger.exception(errmsg)
            return Response(data=errmsg, status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_400_BAD_REQUEST)


# 在派单页面更新订单需要特殊处理
class OrderAllocateUpdate(views.APIView):
    def post(self, request, format=None):
        updateFields = [
            'jancode',
            'product_title',
            'sku_properties_name',
            'receiver_name',
            'receiver_mobile',
            'receiver_address',
            'quantity',
            'payment',
            'price',
        ]
        orderInfo = request.data
        dbOrderObj = Order.objects.get(id=orderInfo['id'])
        if not dbOrderObj.inventory:  # Not allocation
            for f in updateFields:
                setattr(dbOrderObj, f, orderInfo[f])
            dbOrderObj.save()
        else:  # rollback allocate
            with transaction.atomic():
                productObj = Product.objects.get(jancode=orderInfo['jancode'])
                stockObj = Stock.objects.get(
                    product=productObj, inventory=dbOrderObj.inventory)
                stockObj.preallocation = F(
                    'preallocation') - dbOrderObj.quantity
                stockObj.save()
                for f in updateFields:
                    setattr(dbOrderObj, f, orderInfo[f])
                dbOrderObj.status = '待处理'
                dbOrderObj.need_purchase = None
                dbOrderObj.shipping = None
                dbOrderObj.inventory = None
                dbOrderObj.save()
        return Response(status=status.HTTP_200_OK)


# 把订单拽会到预处理, 回滚派单占用库存(需要考虑购物车订单)
# 1. 根据提交的订单号, 查询所有满足条件的订单(天狗购物车会拆成id-1,id-2),
# 2. 订单状态需要在处理中的状态
# 3. 回滚所有占用的库存
# 4. 不考虑关联采购单,直接设置为空, 保留了订单派单时间
# 5. 设置正确的订单状态
class OrderRollbackToPreprocess(views.APIView):
    def post(self, request, format=None):
        orderid = request.data['orderid']
        dbOrderObjs = Order.objects.filter(
            orderid__contains=orderid,
            status__in=[
                '待处理',
                '待采购',
                '已采购',
                '需介入',
                '待发货',
            ],
        )
        with transaction.atomic():
            for dbOrderObj in dbOrderObjs:
                productObj = Product.objects.get(jancode=dbOrderObj.jancode)
                try:
                    stockObj = Stock.objects.get(
                        product=productObj, inventory=dbOrderObj.inventory)
                    stockObj.preallocation = F(
                        'preallocation') - dbOrderObj.quantity
                    stockObj.save()
                except Stock.DoesNotExist:
                    continue
                if dbOrderObj.purchaseorder:
                    if dbOrderObj.purchaseorder.memo:
                        dbOrderObj.purchaseorder.memo = dbOrderObj.purchaseorder.memo + ',' + dbOrderObj.orderid
                    else:
                        dbOrderObj.purchaseorder.memo = dbOrderObj.orderid
                    dbOrderObj.purchaseorder.save()
                dbOrderObj.status = '待处理'
                dbOrderObj.need_purchase = None
                dbOrderObj.shipping = None
                dbOrderObj.inventory = None
                dbOrderObj.purchaseorder = None
                dbOrderObj.save()

        return Response(status=status.HTTP_200_OK)


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


# 采购标记订单疑难
class OrderMarkConflict(views.APIView):
    # TODO: 分页
    #
    # 流程:
    #   1. 修改订单状态为: 需介入.
    #   2. 标记订单状态conflict字段
    #
    def put(self, request, format=None):
        data = request.data

        with transaction.atomic():
            for i in data:
                # mark conflict
                shipping = Shipping.objects.get(id=i['shipping'])
                inventory = Inventory.objects.get(id=i['inventory'])
                i.pop('shipping_name')
                i.pop('inventory_name')
                i.pop('db_number')
                i.pop('purchaseorder_orderid')
                i.pop('shippingdb_delivery_time')
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
        data = request.data

        with transaction.atomic():
            if '已删除' in data['status']:  # 退款
                stockObj = Stock.objects.get(
                    inventory=data['inventory'],
                    product__jancode=data['jancode'])
                stockObj.preallocation = F('preallocation') - data['quantity']
                stockObj.save()
                orderObj = Order.objects.get(id=data['id'])
                orderObj.status = '已删除'
                orderObj.conflict_feedback = data['conflict_feedback']
                orderObj.save(update_fields=['status', 'conflict_feedback'])
            else:  # 更换
                orderObj = Order.objects.get(id=data['id'])
                if orderObj.jancode != data['jancode']:
                    # 判断新jancode库存是否满足
                    stockObj = None
                    try:
                        stockObj = Stock.objects.get(
                            inventory=data['inventory'],
                            product__jancode=data['jancode'])
                    except Stock.DoesNotExist:  # 如果第一次分配到该仓库, 主动在该仓库新建产品记录
                        if not Product.objects.filter(
                                jancode=data['jancode']).exists():
                            errmsg = {'errmsg': '商品库中无该商品, 请先创建产品资料'}
                            return Response(
                                data=errmsg,
                                status=status.HTTP_400_BAD_REQUEST)
                        stockObj = Stock(
                            product=Product.objects.get(
                                jancode=data['jancode']),
                            inventory=Inventory.objects.get(
                                id=data['inventory']),
                            quantity=0,
                            inflight=0,
                            preallocation=0)
                        stockObj.save()

                    # 回滚旧的jancode库存占用
                    rollbackStockObj = Stock.objects.get(
                        inventory=orderObj.inventory,
                        product__jancode=orderObj.jancode)
                    rollbackStockObj.preallocation = F(
                        'preallocation') - data['quantity']
                    rollbackStockObj.save()

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
                            'preallocation') + data['quantity']
                    orderObj.allocate_time = arrow.now().format(
                        'YYYY-MM-DD HH:mm:ss')  # 需要更新订单分配时间
                    orderObj.conflict_feedback = data['conflict_feedback']
                    orderObj.save()
                    stockObj.save()
                else:  # 用户没有做任何操作, 直接改订单状态为待采购
                    orderObj.status = '待采购'
                    orderObj.conflict_feedback = data['conflict_feedback']
                    orderObj.save(
                        update_fields=['status', 'conflict_feedback'])

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
        data = request.data

        orderObj = Order.objects.get(id=data['id'])
        with transaction.atomic():
            if '待处理' in orderObj.status:  # 直接标记删除
                orderObj.status = '已删除'
                orderObj.conflict_feedback = data['conflict_feedback']
                orderObj.save()
            elif ('待发货' in orderObj.status or '需介入' in orderObj.status
                  or '已采购' in orderObj.status
                  or '待采购' in orderObj.status):  # 清除占用的库存
                stockObj = Stock.objects.get(
                    inventory=orderObj.inventory,
                    product__jancode=orderObj.jancode)
                stockObj.preallocation = F('preallocation') - orderObj.quantity
                stockObj.save()
                orderObj.status = '已删除'
                orderObj.conflict_feedback = data['conflict_feedback']
                orderObj.save()
            elif '已删除' in orderObj.status:
                pass
            else:  # 不可删除, 已经分配DB单号, 需要先删除DB单号, 或者已经发货, 无法删除
                errmsg = {'errmsg': '订单已分配面单, 无法删除'}
                return Response(
                    data=errmsg, status=status.HTTP_400_BAD_REQUEST)

            return Response(status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)
