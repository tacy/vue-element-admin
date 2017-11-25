from rest_framework.test import APITestCase

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status

from stock.models import (Order, Stock, Inventory, Product, Supplier,
                          PurchaseOrder, PurchaseOrderItem)
ord = {
    "buyer_remark": "保湿红色",
    "receiver_idcard": None,
    "jancode": "11417081900023",
    "seller_name": "东京彩虹桥",
    "channel_name": "洋码头",
    "orderid": "100000000",
    "receiver_name": "李灵芝",
    "receiver_address": "湖南省,永州市,祁阳县,湖南省永州市祁阳县望吾园二小区五栋一楼",
    "receiver_zip": "426100",
    "receiver_mobile": "15074622111",
    "quantity": 1,
    "price": "222.00",
    "payment": 0,
    "delivery_type": "官方（贝海）直邮",
    "piad_time": "2017-07-07 14:09:57",
    "product_title": "直邮三盒价 每盒仅74！皇后的秘密quality first钻石女王面膜",
    "sku_properties_name": "尺码分类:三盒直邮价,颜色分类:红色高保湿",
    "status": "待处理",
}

stock = {
    "quantity": 0,
    "inflight": 0,
    "preallocation": 0,
    "location": "XYvGbJ77",
    "stock_alert": 1,
}


class OrderAPITests(APITestCase):
    '''
    jancode = [1:11417081900023, 2:4589923572727, 3:4560414840143, 4:10617081900013, 8:0305JP06101089:宁波, 97:4964596457814:郑州]
    supplier = [1: amazon, 2: rakuten, 12: tokyo]
    inventory = [1:xlobo,3:domestic,4:tokyo]
    shipping = [1:1:贝海虚仓电商, 2:1:贝海直邮电商, 5:3:拼邮, 5:16:轨迹, 6:4:直邮电商, 8:4:ems, 9:4:epack, 18:4:日本国内]
    '''
    # 初始数据加载，可使用manage.py dumpdata [app_label app_label app_label.Model]生成
    # xml/yaml/json格式的数据
    # 一般放在每个应用的fixtures目录下, 只需要填写json文件名即可，django会自动查找
    # 此测试类运行结束后，会自动从数据库里销毁这份数据
    # fixtures = ['user.json']
    fixtures = ['initial']

    def setUp(self):
        # 在类里每个测试方法执行前会运行
        # 在此方法执行前，django会运行以下操作
        # 1. 重置数据库，数据库恢复到执行migrate后的状态
        # 2. 加载fixtures数据
        # 所以每个测试方法里对数据库的操作都是独立的，不会相互影响
        user = User.objects.get(username='tacy_lee')
        self.client.force_authenticate(user=user)

        # 准备库存数据(有库存,无库存,有在途库存)
        stock.update({
            'inventory': Inventory.objects.get(id=4),
            'product': Product.objects.get(id=1)
        })
        Stock(**stock).save()
        stock.update({'quantity': 1, 'product': Product.objects.get(id=2)})
        Stock(**stock).save()
        stock.update({
            'quantity': 0,
            'inflight': 1,
            'product': Product.objects.get(id=3)
        })
        Stock(**stock).save()

        # 采购单数据
        PurchaseOrder(**({
            "inventory": Inventory.objects.get(id=4),
            "supplier": Supplier.objects.get(id=1),
            "orderid": "1",
            "status": "在途中",
            "create_time": "2017-09-08 22:02:08",
        })).save()
        PurchaseOrderItem(
            **({
                'product': Product.objects.get(id=3),
                'purchaseorder': PurchaseOrder.objects.get(orderid=1),
                'quantity': 1,
            })).save()

    def tearDown(self):
        # 在类里每个方法结束执行后会运行
        pass

    def test_order_create(self):
        """APP用户登录接口成功情况"""
        # path使用硬编码，不要使用reverse反解析url，以便在修改url之后能及时发现接口地址变化，并通知接口使用人员
        url = reverse('createOrder')
        response = self.client.post(url, ord)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)

    def test_order_allocate_single(self):
        """测试单个订单派单"""
        # path使用硬编码，不要使用reverse反解析url，以便在修改url之后能及时发现接口地址变化，并通知接口使用人员
        url = '/stock/order/allocate/'

        data = [
            {
                'ord': {
                    'orderid': '100000000',
                    'jancode': '11417081900023',
                    'receiver_name': '1',
                },
                'payload': {
                    'id': 1,
                    'orderid': '100000000',
                    'jancode': '11417081900023',
                    'inventory': 4,
                    'shipping': 6,
                },
                'result': {
                    'status': '待采购',
                    'need_purchase': 1,
                    'preallocation': 1,
                    'purchaseorder': None,
                }
            },
            {
                'ord': {
                    'orderid': '100000001',
                    'jancode': '4589923572727',
                    'receiver_name': '2',
                },
                'payload': {
                    'id': 1,
                    'orderid': '100000001',
                    'jancode': '4589923572727',
                    'inventory': 4,
                    'shipping': 6,
                },
                'result': {
                    'status': '需面单',
                    'need_purchase': None,
                    'preallocation': 1,
                    'purchaseorder': None,
                }
            },
            {
                'ord': {
                    'orderid': '100000002',
                    'jancode': '4560414840143',
                    'receiver_name': '3',
                },
                'payload': {
                    'id': 1,
                    'orderid': '100000002',
                    'jancode': '4560414840143',
                    'inventory': 4,
                    'shipping': 6,
                },
                'result': {
                    'status': '已采购',
                    'need_purchase': 1,
                    'preallocation': 1,
                    'purchaseorder': PurchaseOrder.objects.get(id=1),
                }
            },
        ]

        for d in data:
            ord.update(d['ord'])
            Order(**ord).save()
            response = self.client.put(url, d['payload'])
            o = Order.objects.get(orderid=d['ord']['orderid'])
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(o.status, d['result']['status'])
            self.assertEqual(o.need_purchase, d['result']['need_purchase'])
            self.assertEqual(o.purchaseorder, d['result']['purchaseorder'])
            self.assertEqual(
                Stock.objects.get(
                    product__jancode=d['ord']['jancode'],
                    inventory__id=4).preallocation,
                d['result']['preallocation'])
