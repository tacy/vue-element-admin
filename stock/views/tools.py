import base64
import logging
from django.http import HttpResponse

from django.db import connection, transaction
from openpyxl import Workbook
from openpyxl.writer.excel import save_virtual_workbook
from rest_framework import status, views
from rest_framework.response import Response

from stock.models import Order

YMTKEY = {
    '东京彩虹桥': {
        'appid': 'llzlHWWDTkEsUUjwKf',
        'appsecret': 'xdP5yraJQdpypKZNQ0M0zqE35dcrEWox',
        'authcode': 'Ul1BpFlBHdLR6EnEv75RV6QeradgjdBk'
    },
    '妈妈宝宝日本馆': {
        'appid': 'B9EBxjEN4JYB58BG4B',
        'appsecret': 'AKiwySBsiIwqz2TkkgQPXOJgCooc97Jt',
        'authcode': '6SJRmS03o6kwoYjqNPjUXocfMK0MpLhT'
    }
}

access_token = 'AESaZpmFNNcLRbNFmWK38S2ELvpzwjHkRjkpJkNmaaRIpEJ7T+FYBfVvoekui/2k1g=='
client_secret = 'APvYM8Mt5Xg1QYvker67VplTPQRx28Qt/XPdY9D7TUhaO3vgFWQ71CRZ/sLZYrn97w=='.lower(
)
client_id = '8417db83-360c-4275-974f-cf9a2734d8f8'
uex_user = '2830020@qq.com'
uex_passwd = '20162017'

# debug
# access_token = 'ACiYUZ6aKC48faYFD6MpvbOf73BdE9OV5g15q1A6Ghs+i/XIawq/9RHJCzc6Y3UNxA=='
# client_secret = 'APvYM8Mt5Xg1QYvker67VplTPQRx28Qt/XPdY9D7TUhaO3vgFWQ71CRZ/sLZYrn97w=='.lower(
# )
# client_id = '68993573-E38D-4A8A-A263-055C401F9369'

logger = logging.getLogger(__name__)


class ExportBondedOrder(views.APIView):
    def get(self, request, format=None):
        excel_data = [
            ['header1', 'header2', 'header3', 'header4', 'header5'],
            [1, 4, 5, 6, 7],
            [5, 6, 2, 4, 8],
        ]

        if excel_data:
            wb = Workbook(write_only=True)
            ws = wb.create_sheet(title='主表')
            ws2 = wb.create_sheet(title='从表')
            for line in excel_data:
                ws.append(line)
                ws2.append(line)

        response = HttpResponse(
            content_type=
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=mydata.xlsx'

        wb.save(response)

        return response


class ExportDomesticOrder(views.APIView):
    def post(self, request, format=None):
        ords = request.data
        excel_data = [
            [
                '订单号',
                '收件人',
                '固话',
                '手机',
                '地址',
                '明细',
                '发件人',
                '发件人电话',
                '发件人地址',
                '备注',
                '代收金额',
                '保价金额',
                '业务类型',
            ],
        ]

        for o in ords:
            if '拼邮' not in o['shipping_name'] or '已发货' in o['status']:
                errmsg = {'errmsg': '订单:%s物流方式非拼邮或者状态为已发货' % (o['orderid'])}
                return Response(
                    data=errmsg, status=status.HTTP_400_BAD_REQUEST)
            excel_data.append([
                o['orderid'],
                o['receiver_name'],
                o['receiver_mobile'],
                o['receiver_mobile'],
                o['receiver_address'],
                o['product_title'],
                o['seller_name'],
                '13922442299',
                '',
                '',
                '',
                '',
                '',
            ])
        if excel_data:
            wb = Workbook(write_only=True)
            ws = wb.create_sheet(title='主表')
            for line in excel_data:
                ws.append(line)

        # response = HttpResponse(
        #     content_type=
        #     'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        # )
        # response['Content-Disposition'] = 'attachment; filename=mydata.xlsx'
        # wb.save(response)

        # https://stackoverflow.com/questions/8469665/saving-openpyxl-file-via-text-and-filestream
        base64Data = base64.b64encode(save_virtual_workbook(wb))
        msg = {'tableData': base64Data}
        with transaction.atomic():
            for o in ords:
                Order.objects.filter(id=o['id']).update(export_status='已导出')

        return Response(data=msg, status=status.HTTP_200_OK)


class CategoryGet(views.APIView):
    def get(self, request, format=None):
        sql = 'select b.category_id category_id, b.category_cn_name category_cn_name, a.category_id category_parent_id, a.category_cn_name category_parent_cn_name, a.category_version category_version from stock_category a join stock_category b on (a.category_id=b.category_parent_id)'

        def dictfetchall(cursor):
            "Return all rows from a cursor as a dict"
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

        with connection.cursor() as c:
            c.execute(sql)
            results = dictfetchall(c)
            relationData = {}
            for i in results:
                dictkey = i['category_parent_id'].zfill(5)
                if dictkey in relationData:
                    relationData[dictkey]['children'].append({
                        'label':
                        i['category_cn_name'],
                        'value':
                        i['category_id']
                    })
                else:
                    relationData[dictkey] = {
                        'label':
                        i['category_parent_cn_name'],
                        'value':
                        i['category_parent_id'],
                        'children': [
                            {
                                'label': i['category_cn_name'],
                                'value': i['category_id']
                            },
                        ]
                    }

            sortData = [relationData[i] for i in sorted(relationData.keys())]
            data = {
                'results': sortData,
            }
            return Response(data=data, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)
