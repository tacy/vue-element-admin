import django_filters.rest_framework
from .serializers import PurchaseOrderSerializer, ProductSerializer, OrderSerializer
from .models import PurchaseOrder, Product, Order
from rest_framework import generics


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
    filter_fields = ('order_id', 'channel', 'receiver_name', 'jancode')


class OrderDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
