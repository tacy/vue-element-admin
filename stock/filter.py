from django_filters import FilterSet, BaseInFilter, CharFilter, BooleanFilter
from .models import Order


class CharInFilter(BaseInFilter, CharFilter):
    pass


class OrderFilter(FilterSet):
    status = CharInFilter(name='status', lookup_expr='in')
    # http://django-filter.readthedocs.io/en/latest/guide/tips.html?highlight=empty#filtering-by-empty-values
    unshippingdb = BooleanFilter(name='shippingdb', lookup_expr='isnull')
    # https://docs.djangoproject.com/en/dev/ref/models/lookups/#module-django.db.models.lookups
    purchaseorder__orderid = CharFilter(lookup_expr='exact')

    class Meta:
        model = Order
        fields = [
            'orderid',
            'channel_name',
            'inventory',
            'receiver_name',
            'jancode',
            'status',
            'shippingdb',
            'unshippingdb',
        ]
