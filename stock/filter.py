from django_filters import FilterSet, BaseInFilter, CharFilter, BooleanFilter, NumberFilter
from .models import Order, Product, Stock, ShippingDB, PurchaseOrder, PurchaseOrderItem
from django.db.models import F


class CharInFilter(BaseInFilter, CharFilter):
    pass


class NumberRangeFilter(BaseInFilter, NumberFilter):
    pass


class OrderFilter(FilterSet):
    status = CharInFilter(name='status', lookup_expr='in')
    orderid = CharFilter(lookup_expr='icontains')
    # http://django-filter.readthedocs.io/en/latest/guide/tips.html?highlight=empty#filtering-by-empty-values
    unshippingdb = BooleanFilter(name='shippingdb', lookup_expr='isnull')
    # https://docs.djangoproject.com/en/dev/ref/models/lookups/#module-django.db.models.lookups
    purchaseorder__orderid = CharFilter(lookup_expr='exact')
    product_title = CharFilter(lookup_expr='icontains')
    shipping_name = CharFilter(name='shipping__name')

    class Meta:
        model = Order
        fields = [
            'channel_name',
            'inventory',
            'receiver_name',
            'jancode',
            'status',
            'shipping',
            'shippingdb',
            'unshippingdb',
            'sku_properties_name',
            'export_status',
            'delivery_type',
        ]


class ProductFilter(FilterSet):
    # https://docs.djangoproject.com/en/dev/ref/models/lookups/#module-django.db.models.lookups
    name = CharFilter(lookup_expr='icontains')
    brand = CharFilter(lookup_expr='icontains')
    jancode = CharFilter(lookup_expr='icontains')

    class Meta:
        model = Product
        fields = []


class StockFilter(FilterSet):
    jancode = CharFilter(name='product__jancode')
    product_title = CharFilter(name='product__name', lookup_expr='icontains')
    sku_properties = CharFilter(
        name='product__specification', lookup_expr='icontains')
    brand = CharFilter(name='product__brand', lookup_expr='icontains')
    quantity__range = NumberRangeFilter(name='quantity', lookup_expr='range')
    alerting = CharFilter(name='stock_alert', method='filter_alert')

    def filter_alert(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            stock_alert__gt=F('quantity') + F('inflight') - F('preallocation'))

    class Meta:
        model = Stock
        fields = [
            'inventory',
            'stocking_supplier',
        ]


class ShippingDBFilter(FilterSet):
    jancode = CharFilter(name='order__jancode', distinct=True)
    product_title = CharFilter(
        name='order__product_title', lookup_expr='icontains', distinct=True)
    sku_properties_name = CharFilter(
        name='order__sku_properties_name',
        lookup_expr='icontains',
        distinct=True)
    receiver_name = CharFilter(name='order__receiver_name', distinct=True)

    class Meta:
        model = ShippingDB
        fields = [
            'db_number',
            'channel_name',
            'status',
            'shipping',
            'delivery_no',
            'inventory',
            'delivery_time',
            'tax_included_channel',
        ]


class PurchaseOrderFilter(FilterSet):
    orderid = CharFilter(lookup_expr='icontains')
    jancode = CharFilter(
        name='purchaseorderitem__product__jancode', distinct=True)
    product_name = CharFilter(
        name='purchaseorderitem__product__name',
        lookup_expr='icontains',
        distinct=True)

    class Meta:
        model = PurchaseOrder
        fields = [
            'inventory',
            'supplier',
            'status',
        ]


class PurchaseOrderItemFilter(FilterSet):
    inventory = CharFilter(name='purchaseorder__inventory__id')
    orderid = CharFilter(
        name='purchaseorder__orderid', lookup_expr='icontains')
    product_name = CharFilter(
        name='product__name',
        lookup_expr='icontains',
    )
    product_specification = CharFilter(
        name='product__specification',
        lookup_expr='icontains',
    )
    jancode = CharFilter(
        name='product__jancode',
        lookup_expr='icontains',
    )

    class Meta:
        model = PurchaseOrderItem
        fields = [
            'delivery_no',
            'purchaseorder',
            'status',
        ]
