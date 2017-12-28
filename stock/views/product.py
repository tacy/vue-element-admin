import logging

from django.db import transaction
from rest_framework import status, views
from rest_framework.response import Response

from stock.models import Order, Product
from stock.serializers import ProductSerializer

logger = logging.getLogger(__name__)


# 更新产品包括条码
# 更新条码需要同步更新库存表和订单表
class ProductUpdateJancode(views.APIView):
    def post(self, request, format=None):
        data = request.data

        with transaction.atomic():
            productObj = Product.objects.get(id=data['id'])
            jancode = productObj.jancode
            productSerializer = ProductSerializer(
                productObj, data=request.data)
            if productSerializer.is_valid(raise_exception=True):
                productSerializer.save()
                Order.objects.filter(jancode=jancode).update(
                    jancode=data['jancode'],
                    product_title=productObj.name,
                    sku_properties_name=productObj.specification,
                )
                return Response(status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)
