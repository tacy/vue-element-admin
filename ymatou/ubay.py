import asyncio
import hashlib
import logging
import decimal

import aiohttp
import async_timeout

import xmltodict

REQUEST_TIMEOUT = 30
log = logging.getLogger(__name__)


class UbayAPI():
    def __init__(self, session, user_code, password, key):
        self.user_code = user_code
        self.password = password
        self.key = key
        self.session = session

    async def callAPI(self, url, xml, sign):
        data = {
            'user_code': self.user_code,
            'password': self.password,
            'xml': xml,
            'sign': sign,
        }
        log.debug('ubayapi call msg %s', data)
        try:
            with async_timeout.timeout(REQUEST_TIMEOUT):
                async with self.session.post(url, data=data) as response:
                    return await response.text()
        except asyncio.TimeoutError as e:
            log.exception(url, data)
            return None

    async def pushOrder(self, orders):
        url = 'http://open.nxubay.com/API/OrderInfo/createOrder.html'
        rate = decimal.Decimal('0.8')

        address = orders[0]['receiver_address'].split(',')
        msg = {
            'Message': {
                'Body': {
                    'SourcePlatform': 'UBAY',
                    'SourceDealerShop': '21444',
                    'SaleOrderCode': orders[0]['orderid'],
                    'BuyerAccount': orders[0]['receiver_name'],
                    'BuyerNickName': orders[0]['receiver_name'],
                    'Province': address[0],
                    'City': address[1],
                    'District': address[2],
                    'Address': address[3],
                    'ReceiverName': orders[0]['receiver_name'],
                    'ReceiverPhone': orders[0]['receiver_mobile'],
                    'ZipCode': orders[0]['receiver_zip'],
                    'BuyerName': orders[0]['receiver_name'],
                    'IdCard': orders[0]['receiver_idcard'],
                    'OrderPayment': (orders[0]['payment']) * rate,
                    'PostFee': 0,
                    'BuyerPayment': (orders[0]['payment']) * rate,
                    'InsuranceFee': 0,
                    'TaxAmount': 0,
                    'TariffAmount': 0,
                    'AddedValueTaxAmount': 0,
                    'ConsumptionDutyAmount': 0,
                    'PaymentMethod': '29',
                    'PaymentCode': orders[0]['orderid'],
                    'PaymentOrderSeq': '122',
                    'CreateTime': orders[0]['piad_time'],
                    'PayTime': orders[0]['piad_time'],
                    'DistributionCode': '100',
                }
            }
        }
        details = []
        for o in orders:
            item = {
                'Detail': {
                    'ProductNumberCode': o['filing_no'],
                    'SaleGoodsName': o['product_title'],
                    'SaleGoodsPrice': (o['price']) * rate,
                    'SaleNumber': o['quantity'],
                    'SaleSubTotal': (o['price']) * rate * o['quantity'],
                }
            }
            details.append(item)

        msg['Message']['Body']['Details'] = details

        xml = xmltodict.unparse(msg, full_document=False, pretty=True)
        sign = hashlib.md5((self.user_code + self.password + xml +
                            self.key).encode('utf-8')).hexdigest()
        result = await self.callAPI(url, xml, sign)
        return xmltodict.parse(result)

    async def getDeliveryNo(self, orderid):
        url = 'http://open.nxubay.com/API/OrderInfo/getOrderStatus.html'
        msg = {
            'Message': {
                'Body': {
                    'SaleOrderCode': orderid,
                }
            }
        }
        xml = xmltodict.unparse(msg, full_document=False, pretty=True)
        sign = hashlib.md5((self.user_code + self.password + xml +
                            self.key).encode('utf-8')).hexdigest()
        result = await self.callAPI(url, xml, sign)
        return xmltodict.parse(result)


async def main(loop):
    # user_code = 'ubay_test'
    # password = '123456'
    # key = '0000'
    user_code = 'jingdongcaihongqiao'
    password = 'chq123456'
    key = '1013'
    session = aiohttp.ClientSession(loop=loop)
    ubayapi = UbayAPI(session, user_code, password, key)
    result = await ubayapi.getDeliveryNo('127730292-1')
    # result = await ubayapi.pushOrder('')
    print(result)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))

    # Let's also finish all running tasks:
    pending = asyncio.Task.all_tasks()
    result = loop.run_until_complete(asyncio.gather(*pending))
