import asyncio
import base64
import hashlib
import json
import logging
import random
import string
import sys

import arrow
import async_timeout

REQUEST_TIMEOUT = 30
log = logging.getLogger(__name__)


class YmatouAPI():
    def __init__(self, session, appid, appsecret, authcode):
        self.urltpl = 'https://open.ymatou.com/apigateway/v1?app_id={}&method={}'
        self.appid = appid
        self.appsecret = appsecret
        self.authcode = authcode
        self.session = session

    def getSign(self, payload):
        signOrgStr = 'app_id=' + self.appid + '&' + '&'.join(
            [k + '=' + str(payload[k])
             for k in sorted(payload)]) + "&app_secret=" + self.appsecret
        sign = hashlib.md5(signOrgStr.encode('utf-8')).hexdigest().upper()
        return sign

    async def callAPI(self, method, biz_content=None):
        randomstr = ''.join(
            random.choice(string.ascii_letters + string.digits)
            for _ in range(32))
        payload = {
            'auth_code': self.authcode,
            'sign_method': 'MD5',
            'method': method,
            'timestamp': arrow.now().format('YYYY-MM-DD HH:mm:ss'),
            'nonce_str': randomstr,
            # 'biz_content': json.dumps(biz_content)
        }
        if biz_content:
            payload['biz_content'] = json.dumps(biz_content)
        log.debug('call YmatouAPI, method {}, biz_content: {}'.format(
            method, payload['biz_content']))
        payload['sign'] = self.getSign(payload)
        url = self.urltpl.format(self.appid, method)
        try:
            with async_timeout.timeout(REQUEST_TIMEOUT):
                async with self.session.post(url, json=payload) as response:
                    return await response.json()
        except asyncio.TimeoutError as e:
            log.exception(method)
            return None

    async def getOrderList(self, start, end):
        method = 'ymatou.order.list.get'
        page_no = 1
        biz_content = {
            'order_status': "17",  # 17接单, 2付款
            'date_type': 4,
            'sort_type': 1,
            'start_date': start,
            'end_date': end,
            'page_no': page_no,
            'page_rows': 100
        }

        # query order by api
        orders = []
        while True:
            result = await self.callAPI(method, biz_content)
            if '0000' not in result.get('code'):
                sys.exit("Get order failed, ErrMsg: {}".format(
                    result['message']))
            orders_info = result['content']['orders_info']
            if not orders_info:
                return orders
            orders.extend(orders_info)
            if len(orders_info) < 100:
                break
            page_no += 1
            biz_content['page_no'] = page_no

        return orders

    async def deliver(self,
                      orderid,
                      dbnumber,
                      develivery_company,
                      domestic=False):
        method = 'ymatou.order.deliver'
        deliver_orders = {
            'order_id': orderid,
            'logistics_company_id': develivery_company,
            'tracking_number': dbnumber,
            # 'is_domestic_delivery': 'false'  # default
        }
        if domestic:
            deliver_orders['is_domestic_delivery'] = 'true'

        biz_content = {'deliver_orders': [deliver_orders]}
        result = await self.callAPI(method, biz_content)
        return result

    async def getOrderInfo(self, orderid):
        method = 'ymatou.order.detail.get'
        biz_content = {
            'order_id': orderid,
        }
        result = await self.callAPI(method, biz_content)
        return result

    async def getProductInfo(self, productid):
        method = 'ymatou.product.detail.get'
        biz_content = {
            'product_id': productid,
        }
        result = await self.callAPI(method, biz_content)
        return result

    async def syncProductStock(self, sku_stocks):
        method = 'ymatou.sku.stock.update'
        biz_content = {
            'sku_stocks': sku_stocks,
        }
        result = await self.callAPI(method, biz_content)
        return result

    async def getLogisticCompany(self):
        method = 'ymatou.logistics.companies.get'
        result = await self.callAPI(method)
        return result


class XloboAPI():
    def __init__(self, session, access_token, client_secret, client_id):
        self.url = 'http://bill.open.xlobo.com/api/router/rest'
        # self.url = 'http://114.80.87.216:8082/api/router/rest'
        self.access_token = access_token
        self.client_secret = client_secret
        self.client_id = client_id
        self.session = session

    async def callAPI(self, method, msg_param):
        enc_msg = self.client_secret + msg_param.lower() + self.client_secret
        # print(enc_msg)
        sign_str = hashlib.md5(base64.b64encode(
            enc_msg.encode('utf-8'))).hexdigest()

        payload = {
            'method': method,
            'v': '1.0',
            'msg_param': msg_param,
            'client_id': self.client_id,
            'access_token': self.access_token,
            'sign': sign_str,
        }

        log.debug('xlobo api debug %s', payload)

        h = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest'
        }
        try:
            with async_timeout.timeout(REQUEST_TIMEOUT):
                async with self.session.post(
                        self.url, data=payload, headers=h) as response:
                    return await response.json()
        except asyncio.TimeoutError as e:
            log.exception(method, enc_msg)
            return None

    async def getCategory(self):
        method = 'xlobo.catalogue.get'
        BusinessNo = str(random.randint(10000000, 99999999))
        msg = {'BusinessNo': BusinessNo}
        msg_param = json.dumps(msg)
        result = await self.callAPI(method, msg_param)
        return result

    async def getLogistic(self):
        method = 'xlobo.hub.get'
        BusinessNo = str(random.randint(10000000, 99999999))
        msg = {'BusinessNo': BusinessNo}
        msg_param = json.dumps(msg)
        result = await self.callAPI(method, msg_param)
        return result

    async def createNoVerification(self, msg):
        method = 'xlobo.labels.createNoVerification'
        BusinessNo = str(random.randint(10000000, 99999999))
        msg['BusinessNo'] = BusinessNo
        msg_param = json.dumps(msg)
        result = await self.callAPI(method, msg_param)
        return result

    async def createFBXBill(self, msg):
        method = 'xlobo.fbx.createfbxbill'
        BusinessNo = str(random.randint(10000000, 99999999))
        msg['BusinessNo'] = BusinessNo
        msg_param = json.dumps(msg)
        result = await self.callAPI(method, msg_param)
        return result

    async def importOrder(self, msg):
        method = 'xlobo.labels.importorder'
        BusinessNo = str(random.randint(10000000, 99999999))
        msg['BusinessNo'] = BusinessNo
        msg_param = json.dumps(msg)
        result = await self.callAPI(method, msg_param)
        return result

    # msg: {"BillCodes":["DB543200315US","DB543200315US"]}
    async def getPDF(self, msg):
        method = 'xlobo.labels.file.getFile10x15'
        BusinessNo = str(random.randint(10000000, 99999999))
        msg['BusinessNo'] = BusinessNo
        msg_param = json.dumps(msg)
        result = await self.callAPI(method, msg_param)
        return result

    async def deleteDBNumber(self, msg):
        method = 'xlobo.labels.delete'
        BusinessNo = str(random.randint(10000000, 99999999))
        msg['BusinessNo'] = BusinessNo
        msg_param = json.dumps(msg)
        result = await self.callAPI(method, msg_param)
        return result
