import datetime
import asyncio
import json
import logging
import os.path
from itertools import groupby

import aiohttp
import aiomysql
import arrow
import async_timeout

import tiangouAPI
import ubay
import ymatouapi
import utils

REQUEST_TIMEOUT = 60
access_token = 'AESaZpmFNNcLRbNFmWK38S2ELvpzwjHkRjkpJkNmaaRIpEJ7T+FYBfVvoekui/2k1g=='
client_secret = 'APvYM8Mt5Xg1QYvker67VplTPQRx28Qt/XPdY9D7TUhaO3vgFWQ71CRZ/sLZYrn97w=='.lower(
)
client_id = '8417db83-360c-4275-974f-cf9a2734d8f8'
db_password = '12345678'

logger = logging.getLogger(__name__)
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

    logger.info('sync ymt order starttime:%s, endtime:%s', st, et)
    orders = await ymtapi.getOrderList(st, et)
    if not orders:
        return
    # insert order to db
    ords = []
    accept_time = ''
    for o in orders:
        if o['accept_time'] > accept_time:
            accept_time = o[
                'accept_time']  # use accept_time as next start time
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
                # price = int(oi['price']) / len(js)
                # payment = int(oi['payment']) / len(js)
                payment = (
                    float(oi['payment']) + float(oi['p_coupon_discount'])
                ) / len(js)
                price = payment / num
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
                    try:
                        receiver_idcard = o['id_cards'][0]['receiver_id_no']
                    except TypeError as e:
                        logger.exception('emergy msg orderid %s, %s',
                                         o['order_id'], jancode)

                it = (o['seller_id'], '洋码头', o['order_id'], o['receiver_name'],
                      o['receiver_address'], o['receiver_zip'],
                      o['receiver_mobile'], receiver_idcard, o['seller_memo'],
                      o['buyer_remark'], jancode, num, price, payment, dt,
                      o['paid_time'], oi['product_title'], sku_properties_name,
                      '待处理', '', oi['product_id'], price, '预售'
                      if o['pre_sale'] else '现货')
                if not oi['product_id']:
                    logger.warning('导入订单丢失product_id: %s', oi)
                ords.append(it)
    insertOrderSQL = (
        'INSERT INTO stock_order '
        '(seller_name, channel_name, orderid, receiver_name, receiver_address, '
        'receiver_zip, receiver_mobile, receiver_idcard, seller_memo, buyer_remark, jancode, '
        'quantity, price, payment, delivery_type, piad_time, product_title, '
        'sku_properties_name, status, channel_delivery_status, product_id, real_price, pre_sale) '
        'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
    )
    insertExportOrderLog = 'INSERT INTO stock_exportorderlog (sellername, start_time, export_time, count) values (%s, %s, %s, %s)'

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.executemany(insertOrderSQL, ords)

            # insert sync order log
            if accept_time and et > accept_time:
                et = accept_time
            await cur.execute(insertExportOrderLog,
                              (sellerName, st, et, len(ords)))
            await conn.commit()


async def syncTGOrder(tgapi, sellerName, pool):
    # result = await tgapi.login()
    # if not result:
    #     return
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

    logger.info('sync tg order starttime:%s, endtime:%s', st, et)
    state = 'Shipping,Processing'
    rs = await tgapi.getOrderList(st, et, state)
    if not rs:
        return

    # insert order to db
    ords = []
    if not rs['success'] or (rs['success'] and not rs.get('data')):
        return
    next_job_start_time = ''
    for o in rs['data']:
        delty = o['receiver']
        receiver_name = delty['name']
        receiver_address = ','.join([
            delty['province'],
            delty['city'],
            # delty['district'],
            delty.get('district', '无'),
            delty['address'],
        ])
        receiver_mobile = delty['phone']
        receiver_idcard = delty['idCard']
        createTime = arrow.get(
            o['payTime'] / 1000).to('local').format('YYYY-MM-DD HH:mm:ss')
        if next_job_start_time < createTime:
            next_job_start_time = createTime
        for i, oi in enumerate(o['orderItems']):
            # 拆单:
            #    1. jancode (jancode*1+jancode*1)
            #    2. payment根据jancode数量平分
            #    3. price根据num平分
            #    4. quantity = num*数量
            orderid = o['id']
            # if i:
            #     orderid = str(orderid) + '-' + str(i)
            js = oi['barcode'].split('+')
            # for k, j in enumerate(js):
            #     if k:
            #         orderid = str(orderid) + '-' + str(k)
            for j in js:
                jinfo = j.split('*')
                jancode = jinfo[0][2:]  # remove JH
                num = oi['quantity']
                payment = oi['payAmount']
                price = payment / num
                product_title = oi['name']
                # product_id = oi[
                #     'activityToProductId']  # https://m.51tiangou.com/product/listing.html?id=11811435
                # sku_properties_name = oi['attrSku'] if oi['attrSku'] else '无'
                product_id = ''
                sku_properties_name = '无'
                if len(jinfo) == 2:
                    num = num * int(jinfo[1])
                    price = price / int(jinfo[1])

                it = (sellerName, '京东', orderid, receiver_name,
                      receiver_address, '100101', receiver_mobile,
                      receiver_idcard, jancode, num, price, payment, '第三方',
                      createTime, product_title, sku_properties_name, '待处理',
                      '', product_id, price)
                ords.append(it)
    insertOrderSQL = (
        'INSERT INTO stock_order '
        '(seller_name, channel_name, orderid, receiver_name, receiver_address, '
        'receiver_zip, receiver_mobile, receiver_idcard, jancode, quantity, '
        'price, payment, delivery_type, piad_time, product_title, sku_properties_name, status, channel_delivery_status, product_id, real_price) '
        'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
    )
    insertExportOrderLog = 'INSERT INTO stock_exportorderlog (sellername, start_time, export_time, count) values (%s, %s, %s, %s)'

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.executemany(insertOrderSQL, ords)

            # insert sync order log
            if next_job_start_time and et > next_job_start_time:
                et = next_job_start_time
            await cur.execute(insertExportOrderLog,
                              (sellerName, st, et, len(ords)))
            await conn.commit()


# 同步码头订单进入贝海, 贝海未提供接口, 模拟OMS导入订单操作实现
# async def syncYmtOrdToXlobo(session):
#     now = arrow.now().to('local')
#     et = now.format('YYYY-MM-DD')
#     st = now.replace(days=(-1)).format('YYYY-MM-DD')

#     # url = 'http://www.xlobo.com/public/login.aspx'
#     # # xlobo login?
#     # if not session.cookie_jar.filter_cookies('http://www.xlobo.com'):
#     #     VIEWSTATE = None
#     #     with async_timeout.timeout(REQUEST_TIMEOUT):
#     #         async with session.get(url) as response:
#     #             r = await response.text()
#     #             soup = BeautifulSoup(r, 'html.parser')
#     #             VIEWSTATE = soup.find(id="__VIEWSTATE")['value']
#     #             VIEWSTATEGENERATOR = soup.find(
#     #                 id="__VIEWSTATEGENERATOR")['value']
#     #             # PUBKEY = soup.find(id="publicKey")['value']
#     #     pd = {
#     #         '__EVENTTARGET':
#     #         'ctl00$MainContent$LoginButton',
#     #         '__EVENTARGUMENT':
#     #         '',
#     #         '__VIEWSTATE':
#     #         VIEWSTATE,
#     #         'ctl00$MainContent$RememberMe':
#     #         'on',
#     #         '__VIEWSTATEGENERATOR':
#     #         VIEWSTATEGENERATOR,
#     #         'ctl00$MainContent$LoginButton':
#     #         '登录',
#     #         'ctl00$MainContent$UserName':
#     #         '东京彩虹桥',
#     #         # 'ctl00$MainContent$Password': 'beihai*2016$riben'
#     #         'rsaPwd':
#     #         'xPSxLHRxWTQOKKa8z8iMxZRqEJnkz1Y4BEGZ64YTt+HEPGbatzTiRbl8y11chfgj68mmlTK04PNs5mbLllBPyh3BiIN7PDdZ7JVx7feA9I0QJAfq2LmxLzEUPA4w6NX09DDJoyZb+0E6vu2yf1mN1t6XSrILNGUXIKC/Y5zbw4M='
#     #     }

#     #     with async_timeout.timeout(REQUEST_TIMEOUT):
#     #         async with session.post(url, data=pd) as response:
#     #             await response.text()

#     h = {'Content-Type': 'application/json; charset=utf-8'}
#     url = 'http://www.xlobo.com/bill/api/oms/createimportbatch'
#     payload = {
#         "channel": 2,
#         "importType": 1,
#         "OrderType": [2, 8, 3, 6],
#         "syncTime": [st, et],
#     }
#     try:
#         with async_timeout.timeout(REQUEST_TIMEOUT):
#             async with session.post(url, json=payload, headers=h) as response:
#                 await response.text()
#     except asyncio.TimeoutError as e:
#         logger.exception("syncYMTOrderToXlobo")


# 扫描订单表, 同步第三方订单到贝海.
# 订单预处理之后, 才进行订单导入工作, 主要考虑订单信息在预处理的时候,
# 会进行更改, 并且有些订单没有经过预处理是无法导入的, 例如订单产品在
# 产品表中不存在, 导致没有类目和规格等问题.
async def syncTpoOrdToXlobo(xloboapi, pool):
    sql = (
        "select a.id, a.channel_name, a.orderid, a.receiver_name, a.receiver_address, "
        "a.receiver_mobile, a.receiver_zip, a.receiver_idcard, a.payment, "
        "a.product_title, a.quantity, a.price, c.category_id, c.category_version, "
        "b.weight, b.brand, b.specification, a.jancode from stock_order as a "
        "inner join stock_product as b on a.jancode=b.jancode "
        "inner join stock_category as c on b.category_id=c.id "
        "where a.channel_name<>'洋码头' and a.shipping_id in (1,2,6) and inventory_id<>3 and a.importstatus is null and a.status in ('待采购', '需面单', '已采购')"
    )
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql)
            rs = await cur.fetchall()
            for orderid, items in groupby(rs, lambda x: x[2]):
                orders = list(items)
                productList = []
                for r in orders:
                    productList.append(
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
                        }, )

                r = orders[0]
                ai = r[4].split(',')

                try:
                    msg_param = {
                        # 'ChannelName': r[1],
                        'ChannelName': '京东',  # 目前只能用JD
                        'OrderCode': r[2],
                        'ReceiverName': r[3],
                        'ReceiverProvince': ai[0].strip(),
                        'ReceiverCity': ai[1].strip(),
                        'ReceiverDistrict': ai[2].strip(),
                        'ReceiverAddress': ai[3].strip(),
                        'receiverMobile': r[5],
                        'ReceiverPostCode': r[6],
                        'ReceiverIdCode': r[7],
                        'PaymentPrice': str(r[8]),
                        'OrderPrice': str(r[8]),
                        'ProductList': productList
                    }
                except IndexError:
                    logger.exception(
                        '导入第三方订单入贝海失败: data error, orderData is {}'.format(r))
                    continue

                result = await xloboapi.importOrder(msg_param)
                if not result:
                    return
                if result.get('Succeed'):
                    await cur.execute(
                        "update stock_order set importstatus='已导入' where orderid=%s",
                        (r[2], ))
                    await conn.commit()
                else:
                    logger.error(
                        "导入第三方订单入贝海失败: xlobo api result: {}, orderData is: {}".
                        format(result, r))


# automatic process ymatou order delivery
async def deliveryYmtOrder(ymtapi, pool, seller):
    # 订单渠道是洋码头, 并且db单中的ymatou字段为空
    sql = "select orderid, db_number, delivery_company from stock_shipping s inner join (select o.orderid, d.db_number, o.shipping_id from stock_order o inner join stock_shippingdb d on o.shippingdb_id=d.id where o.channel_name='洋码头' and o.channel_delivery_status<>'已发货' and seller_name=%s) as t on s.id=t.shipping_id"
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, (seller, ))
            rs = await cur.fetchall()
            dudepOrds = set([(i[0].split('-')[0], i[1], i[2]) for i in rs])
            for i in dudepOrds:
                r = await ymtapi.deliver(i[0], i[1], i[2])
                if not r:
                    continue
                if '0000' in r.get('code') and r.get('content'):
                    info = r['content']['results']
                    if not info or info[0]['exec_success']:
                        await cur.execute(
                            "update stock_order set channel_delivery_status='已发货' where orderid like %s",
                            (i[0] + '%', ))
                        await conn.commit()
                    else:
                        logger.error(
                            'deliveryYmtOrder: %s failed, db: %s, ErrMsg:%s' %
                            (i[0], i[1], info[0]['msg']))


# 推送宁波保税仓订单
async def pushUbayBondedOrder(ubayapi, pool):
    sql = "select * from stock_order o inner join stock_bondedproduct b on o.jancode=b.jancode where o.status='待处理' and export_status is null and channel_name='洋码头' and  b.bonded_name='宁波保税' and receiver_idcard<>''"
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(sql)
            rs = await cur.fetchall()

            # 购物车订单需要合并推送
            ts = set(map(lambda x: x['orderid'], rs))
            nrs = [[y for y in rs if y['orderid'] == x] for x in ts]

            for i in nrs:
                r = await ubayapi.pushOrder(i)
                logger.debug('pushUbayBondedOrder Result: %s', r)
                if not r:
                    continue
                if 'T' in r['Message']['Result'] or '订单号已存在' in r['Message']['ResultMsg']:
                    await cur.execute(
                        "update stock_order set export_status='已推送' where orderid=%s",
                        (i[0]['orderid'], ))
                    await conn.commit()
                else:
                    logger.error('pushUbayBondedOrder: %s failed, ErrMsg:%s' %
                                 (i[0]['orderid'],
                                  r['Message']['ResultMsg']), )


# 获取宁波保税订单运单号
async def getUbayBondedOrderStatus(ubayapi, pool):
    sql = "select orderid from stock_order o inner join stock_bondedproduct b on o.jancode=b.jancode where o.delivery_type='第三方保税' and b.bonded_name='宁波保税' and o.export_status='已推送' and o.status='待处理' and o.channel_name='洋码头' group by orderid"
    expressCompany = {
        u"贝海国际速递（上海保税专用）": "Y125",
        u"中通快递-中国件（ZTO Express）": "Y129",
        u"圆通速递-中国件（YTO Express）": "Y130",
        u"天天快递-中国件（TTK Express）": "Y131",
        u"宅急送-中国件（ZJS Express）": "Y132",
        u"申通快递-中国件（STO Express）": "Y133",
        u"百世汇通-中国件（800bestex）": "Y134",
        u"韵达快递-中国件（Yundaex）": 'Y135',
        u"顺丰速运-中国件（SF-Express）": 'Y136',
        u"乐天速递": 'Y138',
        u"汇通快递": 'Y140',
        u"全峰快递": 'Y141',
        u"优速物流": 'Y027',
        u"中邮物流（CNPL Express）": "Y024",
        u"邮政- EMS（中国件）": 'Y013',
        u"德邦物流（Deppon ）": 'Y102',
        u"全峰快递（Quanfeng）": 'Y029',
    }

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql)
            rs = await cur.fetchall()

            for i in rs:
                r = await ubayapi.getDeliveryNo(i)
                logger.debug('getBondedOrderDeliveryNo OrderID %s Result: %s',
                             i, r)
                if not r:
                    continue
                msg = r['Message']
                if 'T' in msg['Result']:
                    if msg['Status'] in ['00', '01', '99']:
                        continue
                    ec = ''
                    for j, k in expressCompany.items():
                        if msg['Logistics'][:2] in j:
                            ec = k
                    delivery_no = msg['LogisticsNumber']
                    await cur.execute(
                        "update stock_order set status='已发货',domestic_delivery_no=%s,domestic_delivery_company=%s where orderid=%s",
                        (
                            delivery_no,
                            ec,
                            i,
                        ))
                    await conn.commit()
                else:
                    logger.error(
                        'Ubay getDeliveryNo: orderid=%s failed, ErrMsg:%s' %
                        (i, r['Message']['ResultMsg']), )


# automatic process ymatou bonded order delivery
async def deliveryYmtBondedOrder(ymtapi, pool):
    # 订单渠道是洋码头, 并且db单中的ymatou字段为空
    sql = "select orderid, domestic_delivery_no, domestic_delivery_company from stock_order where delivery_type='第三方保税' and domestic_delivery_no is not null and domestic_delivery_company is not null and channel_delivery_status<>'已发货' group by orderid, domestic_delivery_no, domestic_delivery_company"
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql)
            rs = await cur.fetchall()
            for i in rs:
                r = await ymtapi.deliver(i[0], i[1], i[2])
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
                        logger.error(
                            'deliveryYmtBondedOrder: %s failed, ErrMsg:%s' %
                            (i[0], info[0]['msg']))


# automatic process tiangou order delivery
async def deliveryTgOrder(tgapi, pool):
    # 订单渠道是京东, 并且db单中的ymatou字段为空
    # result = await tgapi.login()
    # if not result:
    #     return
    sql = "select orderid, db_number, tiangou_company from stock_shipping s inner join (select o.orderid, d.db_number, o.shipping_id from stock_order o inner join stock_shippingdb d on o.shippingdb_id=d.id where o.channel_name='京东' and channel_delivery_status<>'已发货' and seller_name='天狗') as t on s.id=t.shipping_id"
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql)
            rs = await cur.fetchall()
            for i in rs:
                if '-' in i[0] or 'wx' in i[0]:  # 补发单子或者微信渠道无需渠道后台发货
                    continue
                # payload = {
                #     'orderId': i[0],
                #     'deliveryId': i[2],
                #     'trackingNo': i[1],  # db_number
                # }
                r = await tgapi.shippingOrder(i[0], i[2], i[1])
                if not r:
                    continue
                if r['success']:
                    await cur.execute(
                        "update stock_order set channel_delivery_status='已发货' where orderid=%s",
                        (i[0], ))
                    await conn.commit()
                else:
                    logger.error('deliveryTgOrder:%s failed, ErrMsg: %s' %
                                 (i[0], r['message']))


async def getXloboDeliveryStatus(xloboapi, pool):
    sql = 'select id,db_number from stock_shippingdb where status="已出库" and xlobo_sign is null and db_number like "DB%"'
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql)
            rs = await cur.fetchall()
            for r in rs:
                msg_param = {'BillCodes': [r[1]]}
                result = await xloboapi.getStatus(msg_param)
                if not result:
                    return
                if result['ErrorCount'] == 0:
                    info = result['Result'][0]
                    if len(info['BillStatusList']) >= 2:
                        await cur.execute(
                            "update stock_shippingdb set xlobo_sign='已签收' where id=%s",
                            (r[0], ))
                        await conn.commit()
                        logger.info('面单签收成功, 面单号:%s', r[1])
                else:
                    logger.error(
                        "查询面单状态失败: xlobo api result: {}, 面单号 is: {}".format(
                            result, r[1]))


async def alertStock(sender, pool):
    sql = 'select p.jancode,p.name,s.inventory_id,s.quantity+s.inflight-s.preallocation, s.stock_alert from stock_stock s inner join stock_product p on p.id=s.product_id where s.stock_alert>0 and s.quantity+s.inflight-s.preallocation<s.stock_alert'
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql)
            rs = await cur.fetchall()
            if rs:
                msg = '\n'.join(['\t'.join(map(str, i)) for i in rs])
                await sender.send(msg)


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
    # username = 'llw-rb'
    # password = '1q2w3e4r5t'
    sessTG = aiohttp.ClientSession(loop=loop)
    tgapi = tiangouAPI.TiangouOpenAPI(sessTG)
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
        loop=loop,
        connector=aiohttp.TCPConnector(verify_ssl=False),
        headers={
            'Content-Type': 'application/json'
        })
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
                               ymtapi, pool, k)))
        # 宁波保税仓发货
        task.append(
            asyncio.ensure_future(
                periodic.start(deliveryYmtBondedOrder,
                               interval['deliveryymtorder'], ymtapi, pool)))

    # sync ymtorder to xlobo
    sessXloboWeb = aiohttp.ClientSession(loop=loop)
    xlobowebapi = ymatouapi.XloboWebAPI(sessXloboWeb)
    task.append(
        asyncio.ensure_future(
            periodic.start(xlobowebapi.syncOrder, interval['impordtoxlobo'],
                           sessXloboWeb)))

    # sync third party to xlobo
    sessTpo = aiohttp.ClientSession(loop=loop)
    xloboapi = ymatouapi.XloboAPI(sessTpo, access_token, client_secret,
                                  client_id)
    task.append(
        asyncio.ensure_future(
            periodic.start(syncTpoOrdToXlobo, interval['impordtoxlobo'],
                           xloboapi, pool)))
    task.append(
        asyncio.ensure_future(
            periodic.start(getXloboDeliveryStatus, interval['pushorder'],
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

    # send stock alert mail
    sender = utils.mailSuite()
    task.append(
        asyncio.ensure_future(
            periodic.start(alertStock, interval['alertStock'], sender, pool)))

    # monitor task change
    task.append(
        asyncio.ensure_future(
            checkTaskChange(periodic, hash(json.dumps(r)), pool)))


logpre = os.path.abspath(__file__)
logging.basicConfig(
    filename='%s.log' % logpre,
    format='%(asctime)s %(levelname)s:%(message)s',
    level=logging.DEBUG)
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
