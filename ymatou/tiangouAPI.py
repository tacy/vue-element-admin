import hashlib
import logging
import asyncio

import aiohttp
import arrow
import async_timeout

REQUEST_TIMEOUT = 30
logger = logging.getLogger(__name__)


class TiangouAPI():
    def __init__(self, session, user, password):
        self.urltpl = 'https://open.ymatou.com/apigateway/v1?app_id={}&method={}'
        self.user = user
        self.password = password
        self.session = session

    async def callAPI(self, url, payload):
        try:
            with async_timeout.timeout(REQUEST_TIMEOUT):
                async with self.session.post(url, data=payload) as response:
                    return await response.json()
        except asyncio.TimeoutError as e:
            logger.exception(url, payload)
            return None

    async def login(self):
        url = 'http://base.51tiangou.com/privates/auth/seller/extLogin'
        payload = {
            'username': self.user,
            'password': self.password,
            'domain': '.51tiangou.com'
        }
        return await self.callAPI(url, payload)

    async def queryOrder(self, page, starttime, endtime):
        url = 'http://oserv.51tiangou.com/privates/seller/orderQuery/queryOrder'
        payload = {
            'stateList': ['Processing', 'Shipping'],
            'receiveMethod': '10',
            'page': page,
            'sort': 'create_time',
            'order': 'asc',
            'createTimeGE': starttime,
            'createTimeLT': endtime,
            'rows': '200',
            'domain': '.51tiangou.com'
        }
        return await self.callAPI(url, payload)

    async def orderItem(self, orderid):
        url = 'http://oserv.51tiangou.com/privates/seller/tgouOrder/orderItem'
        payload = {'orderId': orderid, 'domain': '.51tiangou.com'}
        return await self.callAPI(url, payload)

    # Request URL:http://oserv.51tiangou.com/privates/seller/tgouPackage/matchAndShip
    # Request Method:POST
    # orderId:20036145
    # deliveryVendorId:735
    # trackingNo:ddd  运单号
    # weight:ee
    # shipAmount:ee 运费
    # deliveryId:735
    # domain:.51tiangou.com
    # (uex: 767, japanEMS: 742, xlobo: 735)
    # param: payload {orderId, deliveryVendorId, trackingNo, weight, shipAmount, deliveryId,}
    async def matchAndShip(self, payload):
        url = 'http://oserv.51tiangou.com/privates/seller/tgouPackage/matchAndShip'
        payload['domain'] = '.51tiangou.com'
        return await self.callAPI(url, payload)


class TiangouOpenAPI():
    def __init__(self, session):
        self.urltpl = 'http://open.test.66buy.com.cn/'
        self.appKey = 'kjc'
        self.secrectKey = '583c8063d3be03a96cb50c9c1dfe2c5e'
        self.storeId = '1685'
        self.session = session

    async def callAPI(self, method, action, payload):
        url = self.urltpl + action
        logger.debug(payload)
        try:
            with async_timeout.timeout(REQUEST_TIMEOUT):
                if method == 'get':
                    async with self.session.get(
                            url, params=payload) as response:
                        return await response.json()
                elif method == 'post':
                    async with self.session.get(url, data=payload) as response:
                        return await response.json()
        except asyncio.TimeoutError as e:
            logger.exception(url, payload)
            return None

    async def getToken(self):
        action = 'token'
        method = 'get'
        payload = {'appKey': self.appKey, 'secretKey': self.secrectKey}
        r = await self.callAPI(method, action, payload)
        logger.debug(r)
        return r

    def getSign(self, signStrList):
        signOrgStr = ''.join(sorted(signStrList)) + self.secrectKey
        sign = hashlib.md5(signOrgStr.encode('utf-8')).hexdigest()
        return sign

    async def getOrderList(self, createTimeGE, createTimeLT, stateList):
        action = 'api/order/orderList'
        method = 'get'
        timestamp = arrow.now().timestamp * 1000
        r = await self.getToken()
        token = r['data']['token']
        signList = [createTimeGE, createTimeLT, token]
        signList.extend(stateList)
        sign = self.getSign(signList)
        payload = (
            ('createTimeGE', createTimeGE),
            ('createTimeLT', createTimeLT),
            ('stateList', stateList[0]),
            ('stateList', stateList[1]),
            ('token', token),
            ('sign', sign),
            ('timestamp', str(timestamp)),
        )
        r = await self.callAPI(method, action, payload)
        logger.debug(r)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    with aiohttp.ClientSession(loop=loop) as sess:
        tgOApi = TiangouOpenAPI(sess)
        ct = '2017-12-15 00:00:00'
        et = '2017-12-20 00:00:00'
        stateList = ['Shipping', 'Processing']
        r = loop.run_until_complete(tgOApi.getOrderList(ct, et, stateList))

        print(r)
