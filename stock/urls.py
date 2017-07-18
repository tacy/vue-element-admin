from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework.authtoken import views
from .views import PurchaseOrderList, PurchaseOrderDetail, ProductList, ProductDetail, UserInfo, OrderList, OrderDetail, StockList, StockDetail, ShippingList, AllocationOrder, InventoryList, NeedPurchaseList

urlpatterns = {
    url(r'^login', views.obtain_auth_token),
    url(r'^userinfo', UserInfo.as_view(), name="userdetail"),
    url(r'^pos/$', PurchaseOrderList.as_view(), name="createPO"),
    url(r'^pos/(?P<pk>[0-9]+)/$',
        PurchaseOrderDetail.as_view(),
        name="PODetail"),
    url(r'^product/$', ProductList.as_view(), name="createProduct"),
    url(r'^product/(?P<pk>[0-9]+)/$',
        ProductDetail.as_view(),
        name="ProductDetail"),
    url(r'^order/$', OrderList.as_view(), name="createOrder"),
    url(r'^order/(?P<pk>[0-9]+)/$', OrderDetail.as_view(), name="OrderDetail"),
    url(r'^stock/$', StockList.as_view(), name="createStock"),
    url(r'^stock/(?P<pk>[0-9]+)/$', StockDetail.as_view(), name="StockDetail"),
    url(r'^shipping/$', ShippingList.as_view(), name="createShipping"),
    url(r'^inventory/$', InventoryList.as_view(), name="createInventory"),
    url(r'^order/allocate/$', AllocationOrder.as_view(), name="allocateOrd"),
    url(r'^order/purchase/$', NeedPurchaseList.as_view(), name="purchaseOrd"),
}

urlpatterns = format_suffix_patterns(urlpatterns)
