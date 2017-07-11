import hashlib
import json
import random
import string
import sys

import arrow
import async_timeout

REQUEST_TIMEOUT = 30


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

    async def callAPI(self, method, biz_content):
        randomstr = ''.join(
            random.choice(string.ascii_letters + string.digits)
            for _ in range(32))
        payload = {
            'auth_code': self.authcode,
            'sign_method': 'MD5',
            'method': method,
            'timestamp': arrow.now().format('YYYY-MM-DD HH:mm:ss'),
            'nonce_str': randomstr,
            'biz_content': json.dumps(biz_content)
        }
        payload['sign'] = self.getSign(payload)
        url = self.urltpl.format(self.appid, method)
        with async_timeout.timeout(REQUEST_TIMEOUT):
            async with self.session.post(url, json=payload) as response:
                return await response.json()

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
                sys.exit(
                    "Get order failed, ErrMsg: {}".format(result['message']))
            orders_info = result['content']['orders_info']
            if not orders_info:
                return orders
            orders.extend(orders_info)
            if len(orders_info) < 100:
                break
            page_no += 1
            biz_content['page_no'] = page_no

        return orders
