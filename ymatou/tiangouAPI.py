import asyncio
import logging

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
