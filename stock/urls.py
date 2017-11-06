from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework.authtoken import views
from .views import (
    PurchaseOrderList, PurchaseOrderDetail, ProductList, ProductDetail,
    UserInfo, OrderList, OrderDetail, StockList, StockDetail, ShippingList,
    OrderAllocate, InventoryList, OrderPurchaseList, PurchaseOrderItemList,
    PurchaseOrderItemDetail, SupplierList, OrderPurchase, OrderMarkConflict,
    OrderConflict, NoOrderPurchase, PurchaseOrderDelete, OrderDelete,
    CategoryGet, LogisticGet, XloboCreateNoVerification, ShippingDBList,
    XloboCreateFBXBill, XloboGetPDF, XloboDeleteDBNumber,
    ManualAllocateDBNumber, OrderItemGet, StockOut, OrderTPRCreate,
    PurchaseOrderClear, UexStockOut, ExportBondedOrder, BondedProductList,
    BondedProductDetail, ProductUpdateJancode, SyncStock, ExportDomesticOrder,
    OrderOut, PurchaseOrderTransform, DomesticStockIn, OrderAllocateUpdate,
    OrderRollbackToPreprocess, ExportUexTrack, AddUexNumber, ExportPrint)

urlpatterns = {
    url(r'^login', views.obtain_auth_token),
    url(r'^userinfo', UserInfo.as_view(), name="userdetail"),
    url(r'^purchase/$', PurchaseOrderList.as_view(), name="createPO"),
    url(r'^purchase/(?P<pk>[0-9]+)/$',
        PurchaseOrderDetail.as_view(),
        name="PODetail"),
    url(r'^purchase/item$',
        PurchaseOrderItemList.as_view(),
        name="createPOItem"),
    url(r'^purchase/item(?P<pk>[0-9]+)/$',
        PurchaseOrderItemDetail.as_view(),
        name="POItemDetail"),
    url(r'^product/$', ProductList.as_view(), name="createProduct"),
    url(r'^product/(?P<pk>[0-9]+)/$',
        ProductDetail.as_view(),
        name="ProductDetail"),
    url(r'^product/updatejancode/$',
        ProductUpdateJancode.as_view(),
        name="updateProductJancode"),
    url(r'^bondedproduct/$',
        BondedProductList.as_view(),
        name="createBondedProduct"),
    url(r'^bondedproduct/(?P<pk>[0-9]+)/$',
        BondedProductDetail.as_view(),
        name="BondedProductDetail"),
    url(r'^order/$', OrderList.as_view(), name="createOrder"),
    url(r'^order/(?P<pk>[0-9]+)/$', OrderDetail.as_view(), name="OrderDetail"),
    url(r'^stock/$', StockList.as_view(), name="createStock"),
    url(r'^stock/(?P<pk>[0-9]+)/$', StockDetail.as_view(), name="StockDetail"),
    url(r'^shipping/$', ShippingList.as_view(), name="createShipping"),
    url(r'^shippingdb/$', ShippingDBList.as_view(), name="createShippingdb"),
    url(r'^getcategory/$', CategoryGet.as_view(), name="getCategory"),
    url(r'^inventory/$', InventoryList.as_view(), name="createInventory"),
    url(r'^supplier/$', SupplierList.as_view(), name="createSupplier"),
    url(r'^order/allocate/$', OrderAllocate.as_view(), name="orderAllocate"),
    url(r'^order/allocateupdate/$',
        OrderAllocateUpdate.as_view(),
        name="orderAllocateUpdate"),
    url(r'^stock/out/$', StockOut.as_view(), name="stockOut"),
    url(r'^stock/sync/$', SyncStock.as_view(), name="stockSync"),
    url(r'^order/needpurchase/$',
        OrderPurchaseList.as_view(),
        name="needPurchaseOrd"),
    url(r'^order/purchase/$', OrderPurchase.as_view(), name="orderPurchase"),
    url(r'^order/delete/$', OrderDelete.as_view(), name="orderDelete"),
    url(r'^order/out/$', OrderOut.as_view(), name="orderOut"),
    url(r'^order/createtpr/$', OrderTPRCreate.as_view(),
        name='orderCreateTPR'),
    url(r'^order/items/$', OrderItemGet.as_view(), name="orderItem"),
    url(r'^order/uextrack/$', ExportUexTrack.as_view(), name="uexTrack"),
    url(r'^order/rollback/$',
        OrderRollbackToPreprocess.as_view(),
        name="orderrollback"),
    url(r'^order/markconflict/$',
        OrderMarkConflict.as_view(),
        name="orderMarkConflict"),
    url(r'^order/conflict/$', OrderConflict.as_view(), name="orderConflict"),
    url(r'^order/exportbonded/$',
        ExportBondedOrder.as_view(),
        name="orderBonderdExport"),
    url(r'^order/exportdomestic/$',
        ExportDomesticOrder.as_view(),
        name="orderDomesticExport"),
    url(r'^order/exportprint/$',
        ExportPrint.as_view(),
        name="orderPrintExport"),
    url(r'^purchase/noorderpurchase/$',
        NoOrderPurchase.as_view(),
        name="noOrderConflict"),
    url(r'^purchase/delete/$',
        PurchaseOrderDelete.as_view(),
        name="purchaseOrderDelete"),
    url(r'^purchase/clear/$',
        PurchaseOrderClear.as_view(),
        name="purchaseOrderClear"),
    url(r'^purchase/transform/$',
        PurchaseOrderTransform.as_view(),
        name="purchaseOrderTransform"),
    url(r'^purchase/domesticstockin/$',
        DomesticStockIn.as_view(),
        name="domesticStockIn"),
    url(r'^common/manualallocatedb/$',
        ManualAllocateDBNumber.as_view(),
        name="allocatedbnumber"),
    url(r'^xlobo/getlogistic/$', LogisticGet.as_view(), name="getLogistic"),
    url(r'^xlobo/getpdf/$', XloboGetPDF.as_view(), name="getPDF"),
    url(r'^xlobo/deletedbnumber/$',
        XloboDeleteDBNumber.as_view(),
        name="deleteDBNumber"),
    url(r'^xlobo/createnoverification/$',
        XloboCreateNoVerification.as_view(),
        name="createNoVerification"),
    url(r'^xlobo/createfbxbill/$',
        XloboCreateFBXBill.as_view(),
        name="createFBXBill"),
    url(r'^uex/stockout/$', UexStockOut.as_view(), name="createUexDB"),
    url(r'^uex/addnumber/$', AddUexNumber.as_view(), name="addUexNumber"),
}

urlpatterns = format_suffix_patterns(urlpatterns)
