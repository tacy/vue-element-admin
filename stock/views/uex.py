import logging

from django.db import connection
from rest_framework import status, views
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class AddUexNumber(views.APIView):
    def post(self, request, format=None):
        data = request.data
        start = int(data['start'][2:])
        end = int(data['end'][2:]) + 1
        values = []
        for i in range(start, end):
            values.append(('UE' + str(i), ))
        sql = 'insert into stock_uextrack (uex_number) values(%s)'
        with connection.cursor() as c:
            c.executemany(sql, values)
        return Response(status=status.HTTP_200_OK)
