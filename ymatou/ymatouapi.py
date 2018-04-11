import asyncio
import base64
import hashlib
import json
import logging
import random
import string
import sys

import aiohttp
import arrow
import async_timeout
from bs4 import BeautifulSoup

REQUEST_TIMEOUT = 30
logger = logging.getLogger(__name__)


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
        logger.debug('call YmatouAPI, method {}, biz_content: {}'.format(
            method, payload['biz_content']))
        payload['sign'] = self.getSign(payload)
        url = self.urltpl.format(self.appid, method)
        try:
            with async_timeout.timeout(REQUEST_TIMEOUT):
                async with self.session.post(url, json=payload) as response:
                    return await response.json()
        except asyncio.TimeoutError as e:
            logger.exception(method)
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

        logger.debug('xlobo api debug %s', payload)

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
            logger.exception(method, enc_msg)
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

    async def getStatus(self, msg):
        method = 'xlobo.status.get'
        BusinessNo = str(random.randint(10000000, 99999999))
        msg['BusinessNo'] = BusinessNo
        msg_param = json.dumps(msg)
        result = await self.callAPI(method, msg_param)
        return result


class XloboWebAPI():
    def __init__(self, session):
        self.session = session

    async def login(self):
        url = 'http://www.xlobo.com/public/login.aspx'
        with async_timeout.timeout(REQUEST_TIMEOUT):
            async with self.session.get(url) as response:
                r = await response.text()
                soup = BeautifulSoup(r, 'html.parser')
                VIEWSTATE = soup.find(id="__VIEWSTATE")['value']
                VIEWSTATEGENERATOR = soup.find(
                    id="__VIEWSTATEGENERATOR")['value']
                # PUBKEY = soup.find(id="publicKey")['value']
        pd = {
            '__EVENTTARGET':
            'ctl00$MainContent$LoginButton',
            '__EVENTARGUMENT':
            '',
            '__VIEWSTATE':
            VIEWSTATE,
            'ctl00$MainContent$RememberMe':
            'on',
            '__VIEWSTATEGENERATOR':
            VIEWSTATEGENERATOR,
            'ctl00$MainContent$LoginButton':
            '登录',
            'ctl00$MainContent$UserName':
            '东京彩虹桥',
            # 'ctl00$MainContent$Password': 'beihai*2016$riben'
            'rsaPwd':
            'xPSxLHRxWTQOKKa8z8iMxZRqEJnkz1Y4BEGZ64YTt+HEPGbatzTiRbl8y11chfgj68mmlTK04PNs5mbLllBPyh3BiIN7PDdZ7JVx7feA9I0QJAfq2LmxLzEUPA4w6NX09DDJoyZb+0E6vu2yf1mN1t6XSrILNGUXIKC/Y5zbw4M='
        }
        with async_timeout.timeout(REQUEST_TIMEOUT):
            async with self.session.post(url, data=pd) as response:
                return await response.text()

    async def syncOrder(self):
        if not self.session.cookie_jar.filter_cookies('http://www.xlobo.com'):
            await self.login()
            logger.info('登入xlobo web, 准备通过OMS同步')
        now = arrow.now().to('local')
        et = now.format('YYYY-MM-DD')
        st = now.replace(days=(-1)).format('YYYY-MM-DD')

        h = {'Content-Type': 'application/json; charset=utf-8'}
        url = 'http://www.xlobo.com/bill/api/oms/createimportbatch'
        payload = {
            "channel": 2,
            "importType": 1,
            "OrderType": [2, 8, 3, 6],
            "syncTime": [st, et],
        }
        try:
            with async_timeout.timeout(REQUEST_TIMEOUT):
                async with self.session.post(
                        url, json=payload, headers=h) as response:
                    await response.text()
                    logger.info('通过OMS同步订单完成')
        except asyncio.TimeoutError as e:
            logger.exception("syncYMTOrderToXlobo")


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    appid = 'llzlHWWDTkEsUUjwKf'
    appsecret = 'xdP5yraJQdpypKZNQ0M0zqE35dcrEWox'
    authcode = 'Ul1BpFlBHdLR6EnEv75RV6QeradgjdBk'
    with aiohttp.ClientSession(loop=loop) as sess:
        # api = XloboWebAPI(sess)
        # # ct = '2018-04-03 10:00:00'
        # # et = '2018-04-03 11:00:00'
        # # state = 'Shipping,Processing'
        api = YmatouAPI(sess, appid, appsecret, authcode)
        r = loop.run_until_complete(api.getOrderInfo('133212596'))
        print(r)
        # r = loop.run_until_complete(tgOApi.shippingOrder('1', '1', '1'))
        # print(r)
