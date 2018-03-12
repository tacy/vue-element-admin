import arrow
from django.db import transaction
from django.db.models import F, IntegrityError
from rest_framework import status, views
from rest_framework.response import Response

from stock.models import (AfterSaleCase, AfterSaleMeta, Inventory, Product,
                          Stock, StockInRecord, StockOutRecord)


def correctStock(ordObj, qty, now):
    prodObj = Product.objects.get(jancode=ordObj.jancode)
    stockObj = Stock.objects.get(inventory=ordObj.inventory, product=prodObj)
    # 记录返库操作stockinrecord(订单漏发, 需要做一个入库操作, 修正之前的错误出库)
    stockIRObj = StockInRecord(
        orderid=ordObj.orderid,
        inventory=ordObj.inventory,
        quantity=qty,
        in_date=now.format('YYYY-MM-DD HH:mm:ss'),
        product=prodObj,
        before_stock_quantity=stockObj.quantity,
        before_stock_inflight=stockObj.inflight,
        before_stock_preallocation=stockObj.preallocation,
    )
    stockIRObj.save()
    # 入库
    stockObj.quantity = F('quantity') + qty
    stockObj.save(update_fields=['quantity'])


class ProcessAfterSale(views.APIView):
    def post(self, request, format=None):
        data = request.data

        ascObj = AfterSaleCase.objects.get(id=data['id'])
        processMethodObj = AfterSaleMeta.objects.get(id=data['process_method'])
        pmName = processMethodObj.name
        ascObj.process_method = processMethodObj
        ordObj = ascObj.order
        now = arrow.now()

        with transaction.atomic():
            # 退运(含退款退运和{错发/换货退运})
            if data['needReturn']:
                if not data['isRefund']:  # 属于重发或者补发退运
                    if data['isDamagedNotReturn']:  # 破损不退运
                        pass
                    else:
                        ascObj.return_product = Product.objects.get(
                            jancode=data['return_jancode'])
                        ascObj.return_quantity = data['return_quantity']
                else:  # 退款
                    amount = data['return_amount']  # 退款都用负数表示
                    if amount > 0:
                        amount = -amount
                    if data['isDamagedNotReturn']:  # 破损不退运
                        ascObj.balance_price = data['return_amount']
                    elif data['isOnlyRefund']:  # 漏发/丢件情况下, 只退款(或同时修正库存)
                        if ascObj.case_type.name == '漏发':
                            correctStock(ordObj, data['return_quantity'], now)
                        ascObj.balance_price = data['return_amount']
                    else:
                        ascObj.balance_price = data['return_amount']
                        ascObj.return_product = Product.objects.get(
                            jancode=data['return_jancode'])
                        ascObj.return_quantity = data['return_quantity']

            # 保留
            if data['needRetention']:
                if ascObj.case_type.name == '错发':  # 需要调整库存
                    prodObj = Product.objects.get(
                        jancode=data['retention_jancode'])
                    correctStock(ordObj, ordObj.quantity, now)  # 订单产品库存修正

                    # 错发产品库存出库
                    try:
                        stockRetentionObj = Stock.objects.get(
                            inventory=ordObj.inventory, product=prodObj)
                    except Stock.DoesNotExist:
                        stockRetentionObj = Stock(
                            product=prodObj,
                            inventory=ordObj.inventory,
                            quantity=data['retention_quantity'],
                            inflight=0,
                            preallocation=0)
                        stockRetentionObj.save()
                    # 记录错误发出的产品, 出库操作stockoutrecord
                    stockORObj = StockOutRecord(
                        orderid=ordObj.orderid,
                        inventory=ordObj.inventory,
                        quantity=data['retention_quantity'],
                        out_date=now.format('YYYY-MM-DD HH:mm:ss'),
                        product=prodObj,
                        before_stock_quantity=stockRetentionObj.quantity,
                        before_stock_inflight=stockRetentionObj.inflight,
                        before_stock_preallocation=stockRetentionObj.
                        preallocation,
                    )
                    stockORObj.save()
                    # 出库
                    stockRetentionObj.quantity = F(
                        'quantity') - data['retention_quantity']
                    stockRetentionObj.save(update_fields=['quantity'])

                ascObj.balance_price = data['retention_amount']

            # 补发/重发需要新建订单. (注意, 补发需要调整库存)
            if data['needResend']:
                if pmName == '补发':  # 发生在漏发的时候, 漏发库存已经扣减了, 实际并没有出库, 需要修正
                    if ordObj.quantity < data['resend_quantity']:
                        raise IntegrityError()
                    # qty = ordObj.quantity - data['resend_quantity']
                    correctStock(ordObj, data['resend_quantity'], now)
                ordObj.id = None
                ordObj.inventory = None
                ordObj.shipping = None
                ordObj.purchaseorder = None
                ordObj.shippingdb = None
                ordObj.need_purchase = None
                ordObj.importstatus = None
                ordObj.export_status = None
                ordObj.domestic_delivery_no = None
                ordObj.domestic_delivery_company = None
                ordObj.quantity = data['resend_quantity']
                ordObj.channel_name = '京东' if ordObj.delivery_type != '第三方保税' else '洋码头'
                ordObj.seller_memo = '售后单'
                ordObj.orderid = ordObj.orderid + '-' + now.format('MMDD')
                ordObj.status = '待处理'

                # 退货重发, 是用户购买的产品不喜欢, 需要换别的
                # if ascObj.case_type.name == '退换':
                #     prodObj2 = Product.objects.get(
                #         jancode=data['resend_jancode'])
                #     ordObj.jancode = data['resend_jancode']
                #     ordObj.product_title = prodObj2.name
                #     ordObj.sku_properties_name = prodObj2.specification
                prodObj2 = Product.objects.get(jancode=data['resend_jancode'])
                ordObj.jancode = data['resend_jancode']
                ordObj.product_title = prodObj2.name
                ordObj.sku_properties_name = prodObj2.specification
                ordObj.save()

                # 售后单需要关联补发订单
                ascObj.case_order = ordObj

            ascObj.status = '已完成'
            if ascObj.return_product or ascObj.balance_price:
                ascObj.status = '处理中'
                if ascObj.return_product:
                    ascObj.return_status = '处理中'
                if ascObj.balance_price:
                    ascObj.balance_status = '处理中'

            ascObj.save()
            return Response(status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)


class ArriveAfterSale(views.APIView):
    def post(self, request, format=None):
        data = request.data

        ascObj = AfterSaleCase.objects.get(id=data['id'])
        with transaction.atomic():
            if ascObj.case_type.name == '破损':  # 不入库
                pass
            else:
                inventoryObj = Inventory.objects.get(name='广州')
                before_quantity = 0
                try:
                    stockObj = Stock.objects.get(
                        product=ascObj.return_product, inventory=inventoryObj)
                    before_quantity = stockObj.quantity
                    stockObj.quantity = F('quantity') + ascObj.return_quantity
                    stockObj.save(update_fields=['quantity'])
                except Stock.DoesNotExist:
                    stockObj = Stock(
                        product=ascObj.return_product,
                        quantity=ascObj.return_quantity,
                        inventory=inventoryObj,
                        preallocation=0,
                        inflight=0,
                    )
                    stockObj.save()

                # 记录返库操作stockinrecord(记录退运商品入库广州仓)
                stockIRObj = StockInRecord(
                    orderid=ascObj.order.orderid,
                    inventory=inventoryObj,
                    quantity=ascObj.return_quantity,
                    in_date=arrow.now().format('YYYY-MM-DD HH:mm:ss'),
                    product=ascObj.return_product,
                    before_stock_quantity=before_quantity,
                    before_stock_inflight=stockObj.inflight,
                    before_stock_preallocation=stockObj.preallocation,
                )
                stockIRObj.save()

            ascObj.return_status = '已完成'
            if ascObj.balance_price and ascObj.balance_status == '处理中':
                pass
            else:
                ascObj.status = '已完成'
            ascObj.save()
            return Response(status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)


class BalanceAfterSale(views.APIView):
    def post(self, request, format=None):
        data = request.data

        ascObj = AfterSaleCase.objects.get(id=data['id'])
        ascObj.balance_status = '已完成'
        if ascObj.return_product and ascObj.return_status == '处理中':
            print('a')
            pass
        else:
            ascObj.status = '已完成'
            print('b')

        ascObj.save()
        return Response(status=status.HTTP_200_OK)
