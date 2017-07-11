from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from .views import PurchaseOrderList, PurchaseOrderDetail, ProductList, ProductDetail


urlpatterns = {
    url(r'^pos/$', PurchaseOrderList.as_view(), name="create"),
    url(r'^pos/(?P<pk>[0-9]+)/$', PurchaseOrderDetail.as_view(), name="detail"),
    url(r'^product/$', ProductList.as_view(), name="create"),
    url(r'^product/(?P<pk>[0-9]+)/$', ProductDetail.as_view(), name="detail"),
}

urlpatterns = format_suffix_patterns(urlpatterns)
