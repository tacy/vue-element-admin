import django_filters.rest_framework
from .serializers import PurchaseOrderSerializer, ProductSerializer, OrderSerializer, TokenSerializer, StockSerializer, ShippingSerializer
from .models import PurchaseOrder, Product, Order, Stock, Shipping, Inventory
from rest_framework import generics, views, status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.db import transaction


class AllocationOrder(views.APIView):
    def put(self, request, format=None):
        orderInfo = request.data.get('order')
        stockInfo = request.data.get('stock')
        inventory = Inventory.objects.get(name=stockInfo['inventory_name'])
        shipping = Shipping.objects.get(id=orderInfo['order_shipping'])
        stockInfo['inventory_name'] = inventory
        orderInfo['order_inventory'] = inventory
        orderInfo['order_shipping'] = shipping
        # 分配订单需要占库存
        stockInfo[
            'preallocation'] = stockInfo['preallocation'] + orderInfo['quantity']
        # stockSerializer = StockSerializer(data=stockInfo)
        # orderSerializer = OrderSerializer(data=orderInfo)
        # if stockSerializer.is_valid() and orderSerializer.is_valid():
        s = Stock(**stockInfo)
        o = Order(**orderInfo)
        with transaction.atomic():
            s.save()
            o.save()
            return Response(status=status.HTTP_201_CREATED)
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
    filter_fields = ('orderid', 'channel_name', 'receiver_name', 'jancode')


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
    filter_fields = ('shipping_inventory', )
