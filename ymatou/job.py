import asyncio
import datetime

import aiohttp
import arrow
import aiomysql

import ymatouapi

YMTKEY = {
    '2830020@qq.com': {
        'appid': 'llzlHWWDTkEsUUjwKf',
        'appsecret': 'xdP5yraJQdpypKZNQ0M0zqE35dcrEWox',
        'authcode': 'Ul1BpFlBHdLR6EnEv75RV6QeradgjdBk'
    },
    'tacy.lee@gmail.com': {
        'appid': 'B9EBxjEN4JYB58BG4B',
        'appsecret': 'AKiwySBsiIwqz2TkkgQPXOJgCooc97Jt',
        'authcode': '6SJRmS03o6kwoYjqNPjUXocfMK0MpLhT'
    }
}


async def syncYMTOrder(ymtapi, sellerName, pool):
    deliveryType = [
        '', '', u'直邮', u'官方（贝海）直邮', u'第三方保税', u'官方（贝海）保税', '', u'拼邮'
    ]
    et = arrow.now().to('local').format('YYYY-MM-DD HH:mm:ss')

    # get last export order time from stock_exportorderlog as st
    st = None
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                'select max(export_time) from stock_exportorderlog where sellername=%s',
                (sellerName, ))
            r = await cur.fetchone()
            print(r)
            # c = r[0].astimezone(dateutil.tz.gettz('Asia/Shanghai'))
            # print(c)
            offset_one_second = r[0] + datetime.timedelta(seconds=1)
            st = offset_one_second.strftime('%Y-%m-%d %H:%M:%S')

    print(st, et)

    orders = await ymtapi.getOrderList(st, et)

    # insert order to db
    ords = []
    for o in orders:
        for oi in o['order_items_info']:
            it = (sellerName, '洋码头', o['order_id'], o['receiver_name'],
                  o['receiver_address'], o['receiver_zip'],
                  o['receiver_mobile'], o['seller_memo'], o['buyer_remark'],
                  oi['outer_sku_id'], oi['num'], oi['price'],
                  deliveryType[oi['delivery_type']], o['paid_time'],
                  oi['product_title'], oi['sku_properties_name'])
            ords.append(it)
    print(ords)
    insertOrderSQL = 'INSERT INTO stock_order (seller_name, channel_name, orderid, receiver_name, receiver_address, receiver_zip, receiver_mobile, seller_memo, buyer_remark, jancode, quantity, price, delivery_type, piad_time, product_title, sku_properties_name) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
    insertExportOrderLog = 'INSERT INTO stock_exportorderlog (sellername, export_time, count) values (%s, %s, %s)'

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.executemany(insertOrderSQL, ords)

            # insert sync order log
            await cur.execute(insertExportOrderLog, (sellerName, et,
                                                     len(ords)))
            await conn.commit()


# https://stackoverflow.com/questions/37512182/how-can-i-periodically-execute-a-function-with-asyncio
class Periodic:
    def __init__(self):
        self.stop = False

    async def start(self, func, interval, *args):
        while True:
            await func(*args)
            await asyncio.sleep(interval * 60)
            if self.stop:
                break


async def getTaskInterval(pool):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute('select * from stock_task')
            r = await cur.fetchall()
            return r


async def checkTaskChange(periodic, old_hash, pool):
    while True:
        r = await getTaskInterval(pool)
        new_hash = hash(r)
        if new_hash != old_hash:
            periodic.stop = True
            return
        await asyncio.sleep(60)


async def main(loop):
    sess = aiohttp.ClientSession(
        loop=loop, headers={'Content-Type': 'application/json'})
    pool = await aiomysql.create_pool(
        host='127.0.0.1',
        port=3306,
        user='root',
        password='12345678',
        db='ymatou',
        charset='utf8',
        loop=loop)

    # get task info
    r = await getTaskInterval(pool)
    interval = r[0][2]

    periodic = Periodic()

    # sync ymt order
    task = []
    for k, v in YMTKEY.items():
        ymtapi = ymatouapi.YmatouAPI(sess, v['appid'], v['appsecret'],
                                     v['authcode'])
        task.append(
            asyncio.ensure_future(
                periodic.start(syncYMTOrder, interval, ymtapi, k, pool)))
    task.append(
        asyncio.ensure_future(checkTaskChange(periodic, hash(r), pool)))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))

    # Let's also finish all running tasks:
    pending = asyncio.Task.all_tasks()
    loop.run_until_complete(asyncio.gather(*pending))
