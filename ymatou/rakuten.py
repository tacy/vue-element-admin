# https://webservice.rakuten.co.jp/app/list
# applicationId: 1084286491431277402
# application_secret: 9cd99c26f687c0503e0f8626dff8ff4b965900cf
# affiliateId: 1639459f.81d51130.163945a0.0c755060
# Domain allowed for callbacks: www.joyjoyhouse.co.jp
import asyncio
import logging
import aiohttp
import async_timeout

REQUEST_TIMEOUT = 30
logger = logging.getLogger(__name__)


class RakutenAPI():
    def __init__(self, session):
        self.urltpl = 'https://app.rakuten.co.jp/services/api/IchibaItem/Search/'
        self.applicationId = '1084286491431277402'
        self.session = session

    async def callAPI(self, method, action, payload, params=None):
        url = self.urltpl + action
        logger.debug('Call RakutenAPI: action %s, payload: %s', action,
                     payload)
        try:
            with async_timeout.timeout(REQUEST_TIMEOUT):
                if method == 'get':
                    async with self.session.get(
                            url, params=payload) as response:
                        return await response.json()
                elif method == 'post':
                    async with self.session.post(
                            url, params=params, json=payload) as response:
                        return await response.json()
        except asyncio.TimeoutError as e:
            logger.exception(url, payload)
            return None

    async def searchItem(self, jancode):
        action = '20170706'
        method = 'get'
        payload = {
            'format': 'json',
            'keyword': jancode,
            'applicationId': self.applicationId
        }
        r = await self.callAPI(method, action, payload)
        return r


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    with aiohttp.ClientSession(loop=loop) as sess:
        rakutenApi = RakutenAPI(sess)
        jancode = '4589923572727'
        r = loop.run_until_complete(rakutenApi.searchItem(jancode))
        print(r)
