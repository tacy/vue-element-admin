import django_filters.rest_framework
from .serializers import PurchaseOrderSerializer, ProductSerializer, OrderSerializer, TokenSerializer, StockSerializer, ShippingSerializer, InventorySerializer
from .models import PurchaseOrder, Product, Order, Stock, Shipping, Inventory
from rest_framework import generics, views, status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.db import transaction, connection


class AllocationOrder(views.APIView):

    # 派单需要的操作: 1. 占用库存(preallocation); 2. 标记订单需要采购的数量(need_purchase); 3. 修改订单状态(status:待发货/待采购)
    #
    # 派单流程: 派单分为派单和重派, 如果订单的inventory字段为空, 定位为派单;
    # 如果该字段非空, 定义为重派.
    #
    # 需要根据传入订单号, 查询数据库表中对应订单, 判断order_inventory字段内容:
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
        orderInfo = request.data.get('order')
        stockInfo = request.data.get('stock')
        paramInventory = orderInfo['inventory']
        if not paramInventory:  # 传入参数为空, 无效
            return status.HTTP_200_OK
        dborder = Order.objects.get(id=orderInfo['id'])
        dbinventory = dborder.inventory

        rollbackstock = ''
        isStockUpdate = True
        # 计算库存变化
        if not dbinventory:  # 派单
            stockInfo[
                'preallocation'] = stockInfo['preallocation'] + orderInfo['quantity']  # 分配订单需要占库存
        else:  # 重新派单
            if dbinventory.id != paramInventory:  # 重派单, 订单派给了新的仓库, 需要回滚之前的库存占用
                rollbackstock = Stock.objects.get(
                    inventory=dbinventory.id, jancode=orderInfo['jancode'])
                rollbackstock.preallocation = rollbackstock.preallocation - orderInfo['quantity']
                stockInfo[
                    'preallocation'] = stockInfo['preallocation'] + orderInfo['quantity']
            else:  # 重派单, 但是仓库没有改变, 无需对库存做更新
                if dborder.shipping == orderInfo[
                        'shipping']:  # 派单信息没有变化, 无需处理.
                    return status.HTTP_200_OK
                isStockUpdate = False

        # stockSerializer = StockSerializer(data=stockInfo)
        # orderSerializer = OrderSerializer(data=orderInfo)
        # if stockSerializer.is_valid() and orderSerializer.is_valid():

        with transaction.atomic():
            # 计算订单状态
            if isStockUpdate:
                if not stockInfo['inflight']:
                    stockInfo['inflight'] = 0
                purchaseQuantity = stockInfo['preallocation'] - (
                    stockInfo['quantity'] + stockInfo['inflight'])
                if purchaseQuantity > 0:  # 订单需采购
                    orderInfo['need_purchase'] = purchaseQuantity
                    orderInfo['status'] = '待采购'
                else:
                    orderInfo['status'] = '待发货'

            # 更新订单和仓库信息
            relate_inventory = Inventory.objects.get(id=orderInfo['inventory'])
            relate_shipping = Shipping.objects.get(id=orderInfo['shipping'])
            stockInfo['inventory'] = relate_inventory
            orderInfo['inventory'] = relate_inventory
            orderInfo['shipping'] = relate_shipping

            # question: how to serializ dict
            stockInfo.pop('inventory_name')
            orderInfo.pop('inventory_name')
            orderInfo.pop('shipping_name')
            s = Stock(**stockInfo)
            o = Order(**orderInfo)
            s.save()
            o.save()
            # print(s, o, rollbackstock)
            # stockSerializer = StockSerializer(data=stockInfo)
            # orderSerializer = OrderSerializer(data=orderInfo)
            # print(stockSerializer, orderSerializer)
            # if stockSerializer.is_valid() and orderSerializer.is_valid():
            #     stockSerializer.save()
            #     orderSerializer.save()
            if rollbackstock:
                rollbackstock.save()
            return Response(status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class NeedPurchaseList(views.APIView):
    def get(self, request, format=None):
        sql = "select s.jancode, s.product_name product_name, o.sku_properties_name sku_properties_name, count(*) qty from stock_stock s inner join stock_order o where o.jancode=s.jancode and o.status='待采购' and o.inventory_id=%s group by product_name, sku_properties_name"

        def dictfetchall(cursor):
            "Return all rows from a cursor as a dict"
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

        inventory = request.query_params.get('inventory')
        with connection.cursor() as c:
            c.execute(sql, [inventory])
            results = dictfetchall(c)
            print(inventory, results, request.query_params)
            return Response(data=results, status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_BAD_REQUEST)


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
    # filter_fields = ('order_id')


class PurchaseOrderDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer


class ProductList(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend, )
    filter_fields = ('jancode', 'category', 'band')


class ProductDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class OrderList(generics.ListCreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend, )
    filter_fields = ('orderid', 'channel_name', 'receiver_name', 'jancode',
                     'status')


class OrderDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer


class StockList(generics.ListCreateAPIView):
    queryset = Stock.objects.all()
    serializer_class = StockSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend, )
    filter_fields = ('jancode', )


class StockDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Stock.objects.all()
    serializer_class = StockSerializer


class ShippingList(generics.ListCreateAPIView):
    queryset = Shipping.objects.all()
    serializer_class = ShippingSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend, )
    filter_fields = ('inventory', )


class InventoryList(generics.ListCreateAPIView):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend, )
