from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework.authtoken import views
from .views import (
    PurchaseOrderList, PurchaseOrderDetail, ProductList, ProductDetail,
    UserInfo, OrderList, OrderDetail, StockList, StockDetail, ShippingList,
    OrderAllocate, InventoryList, OrderPurchaseList, PurchaseOrderItemList,
    PurchaseOrderItemDetail, SupplierList, OrderPurchase, OrderMarkConflict,
    OrderConflict, NoOrderPurchase, PurchaseOrderDelete, OrderDelete,
    CategoryGet, LogisticGet, XloboCreateNoVerification, CreateJapanEMS,
    YmatouStockUpdate, ShippingDBList, XloboCreateFBXBill, XloboGetPDF,
    JapanEMSPDF, XloboDeleteDBNumber, ManualAllocateDBNumber, OrderItemGet,
    StockOut, OrderTPRCreate, PurchaseOrderClear, UexStockOut,
    ExportBondedOrder, BondedProductList, BondedProductDetail,
    ProductUpdateJancode, SyncStock, ExportDomesticOrder, OrderOut,
    PurchaseOrderTransform, PurchaseOrderItemStockIn, OrderAllocateUpdate,
    OrderRollbackToPreprocess, ExportUexTrack, AddUexNumber, ExportPrint,
    AfterSaleCaseList, AfterSaleMetaList, ProcessAfterSale, ArriveAfterSale,
    BalanceAfterSale, AfterSaleCaseDetail, CostTypeList, CostRecordList,
    CreateCostRecord, TransformDBList, TransformDBDetail, CreateTransformDB,
    IncomeRecordList, CreateIncomeRecord, TransformRecordList,
    TransformRecordDetail, OrderAlert, PurchaseOrderAlert,
    AnalyzeOrderAndPurchase, OrderAnalyzeList, PurchaseAnalyzeList, AnalyzeHot,
    TransformDBDelete, ImportAgentOrder, OrderSorting)

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
    url(r'^purchase/alert$', PurchaseOrderAlert.as_view(), name="poAlert"),
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
    url(r'^order/alert/$', OrderAlert.as_view(), name="AlertOrder"),
    url(r'^order/importagentorder/$', ImportAgentOrder.as_view(), name="ImportAgentOrder"),
    url(r'^order/sorting/$', OrderSorting.as_view(), name="orderSorting"),
    url(r'^stock/$', StockList.as_view(), name="createStock"),
    url(r'^stock/(?P<pk>[0-9]+)/$', StockDetail.as_view(), name="StockDetail"),
    url(r'^shipping/$', ShippingList.as_view(), name="createShipping"),
    url(r'^shippingdb/$', ShippingDBList.as_view(), name="createShippingdb"),
    url(r'^transformdb/$', TransformDBList.as_view(), name="getTransformdb"),
    url(r'^transformdb/create/$',
        CreateTransformDB.as_view(),
        name="createTransformdb"),
    url(r'^transformdb/(?P<pk>[0-9]+)/$',
        TransformDBDetail.as_view(),
        name="transformdbDetail"),
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
    url(r'^aftersale/case/$',
        AfterSaleCaseList.as_view(),
        name="afterSaleCase"),
    url(r'^aftersale/meta/$',
        AfterSaleMetaList.as_view(),
        name="afterSaleMeta"),
    url(r'^aftersale/process/$',
        ProcessAfterSale.as_view(),
        name="afterSaleProcess"),
    url(r'^aftersale/arrive/$',
        ArriveAfterSale.as_view(),
        name="afterSaleArrive"),
    url(r'^aftersale/balance/$',
        BalanceAfterSale.as_view(),
        name="afterSaleBalance"),
    url(r'^aftersale/case/(?P<pk>[0-9]+)/$',
        AfterSaleCaseDetail.as_view(),
        name="AfterSaleCaseDetail"),
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
    url(r'^purchase/transform/delete/$',
        TransformDBDelete.as_view(),
        name="transformDBDelete"),
    url(r'^purchase/itemstockin/$',
        PurchaseOrderItemStockIn.as_view(),
        name="domesticStockIn"),
    url(r'^common/manualallocatedb/$',
        ManualAllocateDBNumber.as_view(),
        name="allocatedbnumber"),
    url(r'^xlobo/getlogistic/$', LogisticGet.as_view(), name="getLogistic"),
    url(r'^xlobo/getpdf/$', XloboGetPDF.as_view(), name="getPDF"),
    url(r'^xlobo/getemspdf/$', JapanEMSPDF.as_view(), name="getEMSPDF"),
    url(r'^xlobo/deletedbnumber/$',
        XloboDeleteDBNumber.as_view(),
        name="deleteDBNumber"),
    url(r'^xlobo/createnoverification/$',
        XloboCreateNoVerification.as_view(),
        name="createNoVerification"),
    url(r'^ymatou/stockupdate/$',
        YmatouStockUpdate.as_view(),
        name="ymatouStockUpdate"),
    url(r'^xlobo/createfbxbill/$',
        XloboCreateFBXBill.as_view(),
        name="createFBXBill"),
    url(r'^xlobo/createems/$', CreateJapanEMS.as_view(), name="createEMS"),
    url(r'^uex/stockout/$', UexStockOut.as_view(), name="createUexDB"),
    url(r'^uex/addnumber/$', AddUexNumber.as_view(), name="addUexNumber"),
    url(r'^finance/cost/type/$', CostTypeList.as_view(), name='costType'),
    url(r'^finance/cost/record/$', CostRecordList.as_view(),
        name='costRecord'),
    url(r'^finance/cost/createrecord/$',
        CreateCostRecord.as_view(),
        name='createCostRecord'),
    url(r'^finance/income/record/$',
        IncomeRecordList.as_view(),
        name='incomeRecord'),
    url(r'^finance/income/createrecord/$',
        CreateIncomeRecord.as_view(),
        name='createIncomeRecord'),
    url(r'^finance/transform/record/(?P<pk>[0-9]+)/$',
        TransformRecordDetail.as_view(),
        name="TransformRecordDetail"),
    url(r'^finance/transform/record/$',
        TransformRecordList.as_view(),
        name='transformRecord'),
    url(r'^analyze/inout/$',
        AnalyzeOrderAndPurchase.as_view(),
        name="analyzeOrderAndPurchase"),
    url(r'^analyze/order/$', OrderAnalyzeList.as_view(), name="analyzeOrder"),
    url(r'^analyze/purchase/$',
        PurchaseAnalyzeList.as_view(),
        name="analyzePurchase"),
    url(r'^analyze/hot/$', AnalyzeHot.as_view(), name="analyzeHot"),
}

urlpatterns = format_suffix_patterns(urlpatterns)
