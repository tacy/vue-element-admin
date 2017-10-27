import django_filters.rest_framework
from rest_framework import generics

from stock.filter import (OrderFilter, ProductFilter, PurchaseOrderFilter,
                          PurchaseOrderItemFilter, ShippingDBFilter,
                          StockFilter)
from stock.models import (BondedProduct, Inventory, Order, Product,
                          PurchaseOrder, PurchaseOrderItem, Shipping,
                          ShippingDB, Stock, Supplier)
from stock.serializers import (
    BondedProductSerializer, InventorySerializer, OrderSerializer,
    ProductSerializer, PurchaseOrderItemSerializer, PurchaseOrderSerializer,
    ShippingDBSerializer, ShippingSerializer, StockSerializer,
    SupplierSerializer, Token, TokenSerializer)


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
    # filter_fields = ('orderid', 'inventory', 'supplier', 'status')
    filter_class = PurchaseOrderFilter


class PurchaseOrderDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer


class PurchaseOrderItemList(generics.ListCreateAPIView):
    queryset = PurchaseOrderItem.objects.all()
    serializer_class = PurchaseOrderItemSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend, )
    filter_class = PurchaseOrderItemFilter


class PurchaseOrderItemDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = PurchaseOrderItem.objects.all()
    serializer_class = PurchaseOrderItemSerializer


class ProductList(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend, )
    # filter_fields = ('jancode', 'category', 'name', 'brand')
    filter_class = ProductFilter


class ProductDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class BondedProductList(generics.ListCreateAPIView):
    queryset = BondedProduct.objects.all()
    serializer_class = BondedProductSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend, )
    filter_fields = ('jancode', 'bonded_name')


class BondedProductDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = BondedProduct.objects.all()
    serializer_class = BondedProductSerializer


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
    filter_class = StockFilter


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
    filter_class = ShippingDBFilter


class InventoryList(generics.ListCreateAPIView):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend, )


class SupplierList(generics.ListCreateAPIView):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend, )
