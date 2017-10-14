import asyncio
import datetime
import json
import logging
import os.path

import aiohttp
import aiomysql
import arrow
import async_timeout
from bs4 import BeautifulSoup

import tiangouAPI
import ymatouapi
import ubay

REQUEST_TIMEOUT = 60
access_token = 'AESaZpmFNNcLRbNFmWK38S2ELvpzwjHkRjkpJkNmaaRIpEJ7T+FYBfVvoekui/2k1g=='
client_secret = 'APvYM8Mt5Xg1QYvker67VplTPQRx28Qt/XPdY9D7TUhaO3vgFWQ71CRZ/sLZYrn97w=='.lower(
)
client_id = '8417db83-360c-4275-974f-cf9a2734d8f8'
db_password = 'asd12288'

# debug
# access_token = 'ACiYUZ6aKC48faYFD6MpvbOf73BdE9OV5g15q1A6Ghs+i/XIawq/9RHJCzc6Y3UNxA=='
# client_secret = 'APvYM8Mt5Xg1QYvker67VplTPQRx28Qt/XPdY9D7TUhaO3vgFWQ71CRZ/sLZYrn97w=='.lower(
# )
# client_id = '68993573-E38D-4A8A-A263-055C401F9369'

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
                'select export_time from stock_exportorderlog where sellername=%s order by id desc limit 1',
                (sellerName, ))
            r = await cur.fetchone()
            # c = r[0].astimezone(dateutil.tz.gettz('Asia/Shanghai'))
            offset_one_second = r[0] + datetime.timedelta(seconds=1)
            st = offset_one_second.strftime('%Y-%m-%d %H:%M:%S')

    orders = await ymtapi.getOrderList(st, et)
    if not orders:
        return
    # insert order to db
    ords = []
    for o in orders:
        for oi in o['order_items_info']:
            # 拆单:
            #    1. jancode (jancode*1+jancode*1)
            #    2. payment根据jancode数量平分
            #    3. price根据num平分
            #    4. quantity = num*数量
            js = oi['outer_sku_id'].split('+')
            for j in js:
                jinfo = j.split('*')
                jancode = jinfo
                num = int(oi['num'])
                price = int(oi['price']) / len(js)
                payment = int(oi['payment']) / len(js)
                sku_properties_name = oi['sku_properties_name'] if oi[
                    'sku_properties_name'] else '无'
                if len(jinfo) == 2:
                    jancode = jinfo[0]
                    jc = jinfo[1] if jinfo[1] else 1  # 可能写成"jancode*", 需要跳过
                    num = int(oi['num']) * int(jc)
                    price = price / int(jc)
                dt = deliveryType[oi['delivery_type']]
                receiver_idcard = ''
                if u'第三方保税' in dt:
                    receiver_idcard = o['id_cards'][0]['receiver_id_no']
                it = (o['seller_id'], '洋码头', o['order_id'], o['receiver_name'],
                      o['receiver_address'], o['receiver_zip'],
                      o['receiver_mobile'], receiver_idcard, o['seller_memo'],
                      o['buyer_remark'], jancode, num, price, payment, dt,
                      o['paid_time'], oi['product_title'], sku_properties_name,
                      '待处理', '', oi['product_id'])
                ords.append(it)
    insertOrderSQL = (
        'INSERT INTO stock_order '
        '(seller_name, channel_name, orderid, receiver_name, receiver_address, '
        'receiver_zip, receiver_mobile, receiver_idcard, seller_memo, buyer_remark, jancode, '
        'quantity, price, payment, delivery_type, piad_time, product_title, '
        'sku_properties_name, status, channel_delivery_status, product_id) '
        'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
    )
    insertExportOrderLog = 'INSERT INTO stock_exportorderlog (sellername, start_time, export_time, count) values (%s, %s, %s, %s)'

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.executemany(insertOrderSQL, ords)

            # insert sync order log
            await cur.execute(insertExportOrderLog, (sellerName, st, et,
                                                     len(ords)))
            await conn.commit()


async def syncTGOrder(tgapi, sellerName, pool):
    result = await tgapi.login()
    if not result:
        return
    et = arrow.now().to('local').format('YYYY-MM-DD HH:mm:ss')

    # get last export order time from stock_exportorderlog as st
    st = None
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                'select export_time from stock_exportorderlog where sellername=%s order by id desc limit 1',
                (sellerName, ))
            r = await cur.fetchone()
            offset_one_second = r[0] + datetime.timedelta(seconds=1)
            st = offset_one_second.strftime('%Y-%m-%d %H:%M:%S')

    rs = await tgapi.queryOrder(1, st, et)
    if not rs:
        return

    # insert order to db
    ords = []
    if not rs.get('data'):
        return
    for o in rs['data']['rows']:
        delty = o['deliveryAddress']
        receiver_name = delty['receiver']
        receiver_address = ','.join([
            delty['province'], delty['city'],
            delty.get('district', '无'), delty['address']
        ])
        receiver_mobile = delty['phone']
        receiver_idcard = delty['cardNumber']
        createTime = arrow.get(
            o['createTime'] / 1000).format('YYYY-MM-DD HH:mm:ss')

        orderItems = await tgapi.orderItem(o['id'])
        if not orderItems:
            return
        for i, oi in enumerate(orderItems['data']):
            # 拆单:
            #    1. jancode (jancode*1+jancode*1)
            #    2. payment根据jancode数量平分
            #    3. price根据num平分
            #    4. quantity = num*数量
            orderid = o['id']
            if i:
                orderid = str(orderid) + '-' + str(i)
            js = oi['barcode'].split('+')
            for k, j in enumerate(js):
                if k:
                    orderid = str(orderid) + '-' + str(k)
                jinfo = j.split('*')
                jancode = jinfo[0][2:]  # remove JH
                num = oi['quantity']
                payment = oi['fenTanAmount']
                price = payment / num
                product_title = oi['name']
                product_id = oi[
                    'activityToProductId']  # https://m.51tiangou.com/product/listing.html?id=11811435
                sku_properties_name = oi['attrSku'] if oi['attrSku'] else '无'
                if len(jinfo) == 2:
                    num = num * int(jinfo[1])
                    price = price / int(jinfo[1])

                it = (sellerName, '京东', orderid, receiver_name,
                      receiver_address, '100101', receiver_mobile,
                      receiver_idcard, jancode, num, price, payment, '第三方',
                      createTime, product_title, sku_properties_name, '待处理',
                      '', product_id)
                ords.append(it)
    insertOrderSQL = (
        'INSERT INTO stock_order '
        '(seller_name, channel_name, orderid, receiver_name, receiver_address, '
        'receiver_zip, receiver_mobile, receiver_idcard, jancode, quantity, '
        'price, payment, delivery_type, piad_time, product_title, sku_properties_name, status, channel_delivery_status, product_id) '
        'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
    )
    insertExportOrderLog = 'INSERT INTO stock_exportorderlog (sellername, start_time, export_time, count) values (%s, %s, %s, %s)'

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.executemany(insertOrderSQL, ords)

            # insert sync order log
            await cur.execute(insertExportOrderLog, (sellerName, st, et,
                                                     len(ords)))
            await conn.commit()


# 同步码头订单进入贝海, 贝海未提供接口, 模拟OMS导入订单操作实现
async def syncYmtOrdToXlobo(session):
    url = 'http://www.xlobo.com/public/login.aspx'
    now = arrow.now().to('local')
    et = now.format('YYYY-MM-DD')
    st = now.replace(days=(-1)).format('YYYY-MM-DD')

    # xlobo login?
    if not session.cookie_jar.filter_cookies('http://www.xlobo.com'):
        VIEWSTATE = None
        with async_timeout.timeout(REQUEST_TIMEOUT):
            async with session.get(url) as response:
                r = await response.text()
                soup = BeautifulSoup(r, 'html.parser')
                VIEWSTATE = soup.find(id="__VIEWSTATE")['value']
        pd = {
            '__EVENTTARGET': 'ctl00$MainContent$LoginButton',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': VIEWSTATE,
            'ctl00$MainContent$UserName': '东京彩虹桥',
            'ctl00$MainContent$Password': 'beihai*2016$riben'
        }

        with async_timeout.timeout(REQUEST_TIMEOUT):
            async with session.post(url, data=pd) as response:
                await response.text()

    h = {'Content-Type': 'application/json; charset=utf-8'}
    url = 'http://www.xlobo.com/Api/OrderImportApi/CreateImportBatch'
    payload = {
        "ImportStartTime": st,
        "Importendtime": et,
        "Channel": 2,
        "OrderNos": "",
        "OrderType": "2,8,3,6,",
        "OrderStatus": "17",
        "BatchType": 1
    }
    try:
        with async_timeout.timeout(REQUEST_TIMEOUT):
            async with session.post(url, json=payload, headers=h) as response:
                r = await response.text()
    except asyncio.TimeoutError as e:
        logging.exception("syncYMTOrderToXlobo")


# 扫描订单表, 同步第三方订单到贝海.
# 订单预处理之后, 才进行订单导入工作, 主要考虑订单信息在预处理的时候,
# 会进行更改, 并且有些订单没有经过预处理是无法导入的, 例如订单产品在
# 产品表中不存在, 导致没有类目和规格等问题.
async def syncTpoOrdToXlobo(xloboapi, pool):
    sql = (
        "select a.id, a.channel_name, a.orderid, a.receiver_name, a.receiver_address, "
        "a.receiver_mobile, a.receiver_zip, a.receiver_idcard, a.payment, "
        "a.product_title, a.quantity, a.price, c.category_id, c.category_version, "
        "b.weight, b.brand, b.specification, a.jancode "
        "from stock_order as a inner join stock_product as b "
        "on a.jancode=b.jancode and a.channel_name='京东' and a.importstatus is null and a.status in ('待采购', '待发货', '已采购') "
        "inner join stock_category as c "
        "on b.category_id=c.id")
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql)
            rs = await cur.fetchall()
            for r in rs:
                ai = r[4].split(',')
                productList = [
                    {
                        'SkuCode': r[17],
                        'SkuName': r[9],
                        'SendCountryName': '日本',
                        'SecondLevelCategoryId': r[12],
                        'CategoryVersion': r[13],
                        'Num': r[10],
                        'Weight': str(r[14]) if r[14] else '0.3',
                        'UnitPrice': str(r[11]),
                        'Brand': r[15],
                        'Specification': r[16]
                    },
                ]
                msg_param = {
                    'ChannelName': r[1],
                    'OrderCode': r[2],
                    'ReceiverName': r[3],
                    'ReceiverProvince': ai[0],
                    'ReceiverCity': ai[1],
                    'ReceiverDistrict': ai[2],
                    'ReceiverAddress': ai[3],
                    'receiverMobile': r[5],
                    'ReceiverPostCode': r[6],
                    'ReceiverIdCode': r[7],
                    'PaymentPrice': str(r[8]),
                    'OrderPrice': str(r[8]),
                    'ProductList': productList
                }
                result = await xloboapi.importOrder(msg_param)
                if not result:
                    return
                if result.get('Succeed'):
                    await cur.execute(
                        "update stock_order set importstatus='已导入' where id=%s",
                        (r[0], ))
                    await conn.commit()
                else:
                    logging.error(result)


# automatic process ymatou order delivery
async def deliveryYmtOrder(ymtapi, pool):
    # 订单渠道是洋码头, 并且db单中的ymatou字段为空
    sql = "select orderid, db_number, delivery_company from stock_shipping s inner join (select o.orderid, d.db_number, o.shipping_id from stock_order o inner join stock_shippingdb d on o.shippingdb_id=d.id where o.channel_name='洋码头' and o.channel_delivery_status<>'已发货') as t on s.id=t.shipping_id"
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql)
            rs = await cur.fetchall()
            for i in rs:
                orderid = i[0].split('-')[0]
                r = await ymtapi.deliver(orderid, i[1], i[2])
                if not r:
                    continue
                if '0000' in r.get('code') and r.get('content'):
                    info = r['content']['results']
                    if info[0]['exec_success']:
                        await cur.execute(
                            "update stock_order set channel_delivery_status='已发货' where orderid=%s",
                            (i[0], ))
                        await conn.commit()
                    else:
                        logging.error(
                            'deliveryYmtOrder: %s failed, ErrMsg:%s' %
                            (i[0], info[0]['msg']))


# 推送宁波保税仓订单
async def pushUbayBondedOrder(ubayapi, pool):
    sql = "select * from stock_order o inner join stock_bondedproduct b on o.jancode=b.jancode where o.status='待处理' and export_status is null and channel_name='洋码头' and  b.bonded_name='宁波保税'"
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(sql)
            rs = await cur.fetchall()

            # 购物车订单需要合并推送
            ts = set(map(lambda x: x['orderid'], rs))
            nrs = [[y for y in rs if y['orderid'] == x] for x in ts]

            for i in nrs:
                r = await ubayapi.pushOrder(i)
                logging.debug('pushUbayBondedOrder Result: %s', r)
                if not r:
                    continue
                if 'T' in r['Message']['Result']:
                    await cur.execute(
                        "update stock_order set export_status='已推送' where orderid=%s",
                        (i[0]['orderid'], ))
                    await conn.commit()
                else:
                    logging.error(
                        'pushUbayBondedOrder: %s failed, ErrMsg:%s' %
                        (i[0]['orderid'], r['Message']['ResultMsg']), )


# 获取宁波保税订单运单号
async def getUbayBondedOrderStatus(ubayapi, pool):
    sql = "select orderid from stock_order o inner join stock_bondedproduct b on o.jancode=b.jancode where o.delivery_type='第三方保税' and b.bonded_name='宁波保税' and o.export_status='已推送' and o.status='待处理' and o.channel_name='洋码头' group by orderid"
    expressCompany = {
        "贝海国际速递（上海保税专用）": "Y125",
        "中通快递-中国件（ZTO Express）": "Y129",
        "圆通速递-中国件（YTO Express）": "Y130",
        "天天快递-中国件（TTK Express）": "Y131",
        "宅急送-中国件（ZJS Express）": "Y132",
        "申通快递-中国件（STO Express）": "Y133",
        "百世汇通-中国件（800bestex）": "Y134",
        "韵达快递-中国件（Yundaex）": 'Y135',
        "顺丰速运-中国件（SF-Express）": 'Y136',
        "乐天速递": 'Y138',
        "汇通快递": 'Y140',
        "全峰快递": 'Y141',
        "优速物流": 'Y027',
        "中邮物流（CNPL Express）": "Y024",
        "EMS（中国件）": 'Y013',
        "德邦物流（Deppon ）": 'Y102',
        "全峰快递（Quanfeng）": 'Y029',
    }

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql)
            rs = await cur.fetchall()

            for i in rs:
                r = await ubayapi.getDeliveryNo(i)
                logging.debug('getBondedOrderDeliveryNo Result: %s', r)
                if not r:
                    continue
                msg = r['Message']
                if 'T' in msg['Result']:
                    if msg['Status'] in ['00', '01']:
                        continue
                    ec = ''
                    for i, k in expressCompany.items():
                        if msg['Logistics'] in i:
                            ec = k
                    delivery_no = msg['LogisticsNumber']
                    await cur.execute(
                        "update stock_order set status='已发货',domestic_delivery_no=%s,domestic_delivery_company=%s where orderid=%s",
                        (i, delivery_no, ec))
                    await conn.commit()
                else:
                    logging.error(
                        'Ubay getDeliveryNo: orderid=%s failed, ErrMsg:%s' %
                        (i, r['Message']['ResultMsg']), )


# automatic process ymatou bonded order delivery
async def deliveryYmtBondedOrder(ymtapi, pool):
    # 订单渠道是洋码头, 并且db单中的ymatou字段为空
    sql = "select orderid, domestic_delivery_no, domestic_delivery_company from stock_order where domestic_delivery_no is not null and domestic_delivery_company is not null group by orderid, domestic_delivery_no, domestic_delivery_company"
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql)
            rs = await cur.fetchall()
            for i in rs:
                r = await ymtapi.deliver(i[0], i[1], i[2], domestic=True)
                if not r:
                    continue
                if '0000' in r.get('code') and r.get('content'):
                    info = r['content']['results']
                    if info[0]['exec_success']:
                        await cur.execute(
                            "update stock_order set channel_delivery_status='已发货' where orderid=%s",
                            (i[0], ))
                        await conn.commit()
                    else:
                        logging.error(
                            'deliveryYmtOrder: %s failed, ErrMsg:%s' %
                            (i[0], info[0]['msg']))


# automatic process tiangou order delivery
async def deliveryTgOrder(tgapi, pool):
    # 订单渠道是京东, 并且db单中的ymatou字段为空
    result = await tgapi.login()
    if not result:
        return
    sql = "select orderid, db_number, tiangou_company from stock_shipping s inner join (select o.orderid, d.db_number, o.shipping_id from stock_order o inner join stock_shippingdb d on o.shippingdb_id=d.id where o.channel_name='京东' and channel_delivery_status<>'已发货' and seller_name='天狗') as t on s.id=t.shipping_id"
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql)
            rs = await cur.fetchall()
            for i in rs:
                if '-' in i[0]:  # 补发单子是否需要发货
                    continue
                payload = {
                    'orderId': i[0],
                    'deliveryVendorId': i[2],
                    'trackingNo': i[1],  # db_number
                    'weight': 500,
                    'shipAmount': 80,
                    'deliveryId': i[2]
                }
                r = await tgapi.matchAndShip(payload)
                if not r:
                    continue
                if r['success']:
                    await cur.execute(
                        "update stock_order set channel_delivery_status='已发货' where orderid=%s",
                        (i[0], ))
                    await conn.commit()
                else:
                    logging.error('deliveryTgOrder:%s failed, ErrMsg: %s' %
                                  (i[0], r['message']))


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
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute('select * from stock_task')
            r = await cur.fetchall()
            return r


async def checkTaskChange(periodic, old_hash, pool):
    while True:
        r = await getTaskInterval(pool)
        new_hash = hash(json.dumps(r))
        if new_hash != old_hash:
            periodic.stop = True
            return
        await asyncio.sleep(60)


async def main(loop):
    pool = await aiomysql.create_pool(
        host='127.0.0.1',
        port=3306,
        user='root',
        password=db_password,
        db='ymatou',
        charset='utf8mb4',
        autocommit=True,
        loop=loop)

    # get task info
    r = await getTaskInterval(pool)
    interval = {i['name']: i['interval'] for i in r}

    periodic = Periodic()
    task = []

    # sync TG order
    username = 'llw-rb'
    password = '1q2w3e4r5t'
    sessTG = aiohttp.ClientSession(loop=loop)
    tgapi = tiangouAPI.TiangouAPI(sessTG, username, password)
    task.append(
        asyncio.ensure_future(
            periodic.start(syncTGOrder, interval['syncorder'], tgapi, '天狗',
                           pool)))
    task.append(
        asyncio.ensure_future(
            periodic.start(deliveryTgOrder, interval['deliveryymtorder'],
                           tgapi, pool)))

    # sync YMT order & delivery ymatou order
    sessYmt = aiohttp.ClientSession(
        loop=loop, headers={'Content-Type': 'application/json'})
    for k, v in YMTKEY.items():
        ymtapi = ymatouapi.YmatouAPI(sessYmt, v['appid'], v['appsecret'],
                                     v['authcode'])
        task.append(
            asyncio.ensure_future(
                periodic.start(syncYMTOrder, interval['syncorder'], ymtapi, k,
                               pool)))
        task.append(
            asyncio.ensure_future(
                periodic.start(deliveryYmtOrder, interval['deliveryymtorder'],
                               ymtapi, pool)))
        # 宁波保税仓发货
        task.append(
            asyncio.ensure_future(
                periodic.start(deliveryYmtBondedOrder, interval[
                    'deliveryymtorder'], ymtapi, pool)))

    # sync ymtorder to xlobo
    sessXlobo = aiohttp.ClientSession(loop=loop)
    task.append(
        asyncio.ensure_future(
            periodic.start(syncYmtOrdToXlobo, interval['impordtoxlobo'],
                           sessXlobo)))

    # sync third party to xlobo
    sessTpo = aiohttp.ClientSession(loop=loop)
    xloboapi = ymatouapi.XloboAPI(sessTpo, access_token, client_secret,
                                  client_id)
    task.append(
        asyncio.ensure_future(
            periodic.start(syncTpoOrdToXlobo, interval['impordtoxlobo'],
                           xloboapi, pool)))

    # push bondedOrder to Ubay
    sessUbay = aiohttp.ClientSession(loop=loop)
    user_code = 'jingdongcaihongqiao'
    password = 'chq123456'
    key = '1013'
    ubayapi = ubay.UbayAPI(sessUbay, user_code, password, key)
    task.append(
        asyncio.ensure_future(
            periodic.start(pushUbayBondedOrder, interval['pushorder'], ubayapi,
                           pool)))
    task.append(
        asyncio.ensure_future(
            periodic.start(getUbayBondedOrderStatus, interval['getdeliveryno'],
                           ubayapi, pool)))

    task.append(
        asyncio.ensure_future(
            checkTaskChange(periodic, hash(json.dumps(r)), pool)))


logpre = os.path.abspath(__file__)
logging.basicConfig(
    filename='%s.log' % logpre,
    format='%(asctime)s %(levelname)s:%(message)s',
    level=logging.INFO)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s %(levelname)s:%(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))

    # Let's also finish all running tasks:
    pending = asyncio.Task.all_tasks()
    loop.run_until_complete(asyncio.gather(*pending))
