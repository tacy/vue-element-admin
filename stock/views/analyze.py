import logging

import arrow
from django.db import transaction, connection
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

        logger.debug('analyze time range [st:%s, et:%s]', start_time, end_time)
        ordsInfo = Order.objects.filter(
            Q(piad_time__range=(start_time, end_time)),
            ~Q(status='已删除'),
            ~Q(delivery_type='第三方保税')).values(
                'jancode',
                'seller_name').annotate(total=Sum('quantity')).order_by()

        poisInfo = PurchaseOrderItem.objects.filter(
            Q(purchaseorder__create_time__range=(start_time, end_time)),
            ~Q(purchaseorder__status='已删除'),
            ~Q(purchaseorder__supplier__in=[12, 18])).values(
                'product').annotate(total=Sum('quantity')).order_by()

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


class AnalyzeHot(views.APIView):
    #
    # postForm: {
    #   type: undefined,  (热门/关键字)
    #   st: undefined,
    #   et: undefined,
    #   q: undefined,
    # },
    #
    def get(self, request, format=None):
        data = request.query_params
        analyze_type = data['analyze_type']
        st = arrow.get(data['st']).format('YYYY-MM-DD HH:mm:ss')
        et = arrow.get(data['et']).format('YYYY-MM-DD HH:mm:ss')
        logger.debug('time range [st:%s, et:%s]', st, et)
        sqls = {
            '热门':
            'select sellerid,product_id,product_name,addtime, count(sellerid) total from addtime>%s and addtime<%s and country="日本" group by sellerid,productid,productname order by total limit 200',
            '关键字':
            'select sellerid,productid,product_name,addtime, "" total from addtime>%s and addtime<%s and country="日本" and lower(productname) LIKE %s'
        }

        def dictfetchall(cursor):
            "Return all rows from a cursor as a dict"
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

        with connection.cursor() as c:
            if analyze_type == '热门':
                c.execute(sqls[analyze_type], (st, et))
            elif analyze_type == '关键字':
                q = data['q']
                c.execute(sqls[analyze_type], (st, et, q))
            rsData = dictfetchall(c)
            return Response(
                data={'results': rsData}, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)
