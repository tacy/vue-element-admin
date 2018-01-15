import logging

import arrow
from django.db import transaction
from django.db.models import F, Q, Sum
from rest_framework import status, views
from rest_framework.response import Response

from stock.models import (Order, OrderAnalyze, Product, PurchaseAnalyze,
                          PurchaseOrderItem)

logger = logging.getLogger(__name__)


class AnalyzeOrderAndPurchase(views.APIView):
    #
    #   postForm: {
    #   analyze_time: undefined,
    # },
    #
    def put(self, request, format=None):
        at = arrow.get(request.data['analyze_time'])
        month = at.format('MMMM').lower()
        yeah = at.format('YYYY')
        start_time = at.floor('month').format('YYYY-MM-DD HH:mm:ss')
        end_time = at.replace(
            months=+1).floor('month').format('YYYY-MM-DD HH:mm:ss')

        ordsInfo = Order.objects.filter(
            Q(piad_time__range=(start_time, end_time)),
            ~Q(status='已删除'),
            ~Q(delivery_type='第三方保税')).values(
                'jancode', 'seller_name').annotate(total=Sum('quantity'))

        poisInfo = PurchaseOrderItem.objects.filter(
            Q(purchaseorder__create_time__range=(start_time, end_time)),
            ~Q(purchaseorder__status='已删除'),
            ~Q(purchaseorder__supplier__in=[12, 18])).values(
                'product').annotate(total=Sum('quantity'))

        with transaction.atomic():
            for o in ordsInfo:
                try:
                    product = Product.objects.get(jancode=o['jancode'])
                except Product.DoesNotExist:
                    logger.exception(o['jancode'])
                    continue
                try:
                    oaObj = OrderAnalyze.objects.get(
                        seller_name=o['seller_name'],
                        product=product,
                        yeah=yeah,
                    )
                    setattr(oaObj, month, o['total'])
                    oaObj.total = F('january') + F('february') + F(
                        'march') + F('april') + F('may') + F('june') + F(
                            'july') + F('august') + F('september') + F(
                                'october') + F('november') + F('december')
                    oaObj.save()
                except OrderAnalyze.DoesNotExist:
                    oa = {
                        'seller_name': o['seller_name'],
                        'yeah': yeah,
                        'product': product,
                        'january': 0,
                        'february': 0,
                        'march': 0,
                        'april': 0,
                        'may': 0,
                        'june': 0,
                        'july': 0,
                        'august': 0,
                        'september': 0,
                        'october': 0,
                        'november': 0,
                        'december': 0,
                        'total': 0,
                    }
                    oa[month] = o['total']
                    oa['total'] = o['total']
                    OrderAnalyze(**oa).save()

            for o in poisInfo:
                try:
                    product = Product.objects.get(id=o['product'])
                except Product.DoesNotExist:
                    logger.exception(o['product'])
                    continue
                try:
                    paObj = PurchaseAnalyze.objects.get(
                        product=product,
                        yeah=yeah,
                    )
                    setattr(paObj, month, o['total'])
                    paObj.total = F('january') + F('february') + F(
                        'march') + F('april') + F('may') + F('june') + F(
                            'july') + F('august') + F('september') + F(
                                'october') + F('november') + F('december')
                    paObj.save()
                except PurchaseAnalyze.DoesNotExist:
                    pa = {
                        'yeah': yeah,
                        'product': product,
                        'january': 0,
                        'february': 0,
                        'march': 0,
                        'april': 0,
                        'may': 0,
                        'june': 0,
                        'july': 0,
                        'august': 0,
                        'september': 0,
                        'october': 0,
                        'november': 0,
                        'december': 0,
                        'total': 0,
                    }
                    pa[month] = o['total']
                    pa['total'] = o['total']
                    PurchaseAnalyze(**pa).save()

            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)
