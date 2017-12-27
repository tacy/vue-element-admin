import logging

import arrow
from django.db import transaction
from rest_framework import status, views
from rest_framework.response import Response

from stock.models import CostRecord, CostType, Inventory

logger = logging.getLogger(__name__)


class CreateCostRecord(views.APIView):
    #
    #   postForm: {
    #   pay_time: undefined,
    #   inventory: undefined,
    #   items: [
    #     {
    #       costtype: undefined,
    #       amount: undefined,
    #       memo: undefined
    #     }
    #   ]
    # },
    #
    def put(self, request, format=None):
        data = request.data
        logger.debug('新建费用支出调试:%s', data)
        pay_time = arrow.get(
            data['pay_time']).to('local').format('YYYY-MM-DD hh:mm:ss')
        inventoryObj = Inventory.objects.get(id=data['inventory'])

        with transaction.atomic():
            for i in data['items']:
                costtype = CostType.objects.get(id=i['costtype'])
                costrecordObj = CostRecord(
                    pay_time=pay_time,
                    inventory=inventoryObj,
                    costtype=costtype,
                    memo=i['memo'],
                    amount=i['amount'],
                )
                costrecordObj.save()
            return Response(data=data, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)
