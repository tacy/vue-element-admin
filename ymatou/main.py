import asyncio
import json

import aiohttp
import aiomysql
import arrow
import async_timeout
import click
import pymysql.cursors
from bs4 import BeautifulSoup

from tiangouAPI import TiangouAPI
from ymatouapi import XloboAPI, YmatouAPI

REQUEST_TIMEOUT = 120
db_password = 'asd12288'


async def fetch(session, url, payload):
    with aiohttp.Timeout(120):
        async with session.post(url, json=payload) as response:
            return await response.text()


async def fetch_all(session, url, payloads, loop):
    results = await asyncio.gather(
        * [fetch(session, url, payload) for payload in payloads],
        return_exceptions=True  # default is false, that would raise
    )

    for idx, payload in enumerate(payloads):
        print('{}: {}'.format(payload['PageNumber'], 'ERR' if isinstance(
            results[idx], Exception) else 'OK'))
    cs = []
    pool = await aiomysql.create_pool(
        host='127.0.0.1',
        port=3306,
        user='root',
        password=db_password,
        db='ymatou',
        charset='utf8mb4',
        loop=loop)
    for a in results:
        d = None
        try:
            d = json.loads(a)
        except json.decoder.JSONDecodeError as e:
            print(e)
            print(a)
        # print(d)
        for o in d['Data']['Products']:
            categoryid = None
            try:
                categoryid = o['CategoryNavigation'].split('>')[1]
            except IndexError as e:
                print(e)
                print(o['CategoryNavigation'])
                categoryid = o['CategoryNavigation']
            if categoryid:
                async with pool.acquire() as conn:
                    async with conn.cursor() as cur:
                        await cur.execute(
                            'select category_id from stock_category where category_cn_name=%s',
                            (categoryid, ))
                        (id, ) = await cur.fetchone()
                        if id:
                            categoryid = id
            it = (o['ProductName'], o['SkuId'], categoryid, o['BrandName'],
                  o['Specification'])
            cs.append(it)
    # click.echo(cs)
    insertProductSQL = 'INSERT INTO stock_product (name, jancode, category_id, brand, specification) VALUES (%s, %s, %s, %s, %s)'

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.executemany(insertProductSQL, cs)
            await conn.commit()
    # return results


async def getCategory(xloboapi, loop):
    rs = await xloboapi.getCategory()
    pool = await aiomysql.create_pool(
        host='127.0.0.1',
        port=3306,
        user='root',
        password=db_password,
        db='ymatou',
        charset='utf8mb4',
        loop=loop)
    cs = []
    version = rs['Result']['Version']
    categorys = rs['Result']['Categorys']
    for o in categorys:
        it = (o['CategoryID'], o['CategoryCnName'], o['CategoryEnName'],
              o['CategoryLevel'], o['CategoryParentId'], version)
        cs.append(it)
    # print(cs)
    insertCategorySQL = 'INSERT INTO stock_category (category_id, category_cn_name, category_en_name, category_level, category_parent_id, category_version) VALUES (%s, %s, %s, %s, %s, %s)'
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.executemany(insertCategorySQL, cs)
            await conn.commit()


async def getTGOrder(tgapi, sellerName):

    await tgapi.login()

    et = arrow.now().to('local').format('YYYY-MM-DD HH:mm:ss')

    # get last export order time from stock_exportorderlog as st
    st = '2017-07-31 00:00:00'

    print(st, et)

    rs = await tgapi.queryOrder(1, st, et)
    click.echo(rs)

    # insert order to db
    ords = []
    for o in rs['data']['rows']:
        delty = o['deliveryAddress']
        orderid = o['id']
        receiver_name = delty['receiver']
        receiver_address = ','.join([
            delty['province'], delty['city'], delty['district'],
            delty['address']
        ])
        receiver_mobile = delty['phone']
        receiver_idcard = delty['cardNumber']
        createTime = arrow.get(
            o['createTime'] / 1000).format('YYYY-MM-DD HH:mm:ss')

        orderItems = await tgapi.orderItem(o['id'])
        click.echo(orderItems)
        for oi in orderItems['data']:
            # 柴单:
            #    1. jancode (jancode*1+jancode*1)
            #    2. payment根据jancode数量平分
            #    3. price根据num平分
            #    4. quantity = num*数量

            js = oi['barcode'].split('+')
            for j in js:
                jinfo = j.split('*')
                jancode = jinfo[0][2:]  # remove JH
                num = oi['quantity']
                payment = oi['fenTanAmount']
                price = payment / num
                product_title = oi['name']
                if len(jinfo) == 2:
                    num = num * int(jinfo[1])
                    price = price / int(jinfo[1])

                it = (sellerName, '京东', orderid, receiver_name,
                      receiver_address, '100101', receiver_mobile,
                      receiver_idcard, jancode, num, price, payment, '第三方',
                      createTime, product_title, '待处理')
                ords.append(it)
    click.echo(ords)


async def importYmtOrderToXlobo(session, loop):
    url = 'http://www.xlobo.com/public/login.aspx'

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

    # {"ImportStartTime":"2017-07-31","Importendtime":"2017-08-04","Channel":2,"OrderNos":"","OrderType":"2,8,3,6,","OrderStatus":"17","BatchType":1}
    # http://www.xlobo.com/Api/OrderImportApi/CreateImportBatch
    h = {'Content-Type': 'application/json; charset=utf-8'}
    url = 'http://www.xlobo.com/Api/OrderImportApi/CreateImportBatch'
    payload = {
        "ImportStartTime": "2017-07-31",
        "Importendtime": "2017-08-04",
        "Channel": 2,
        "OrderNos": "",
        "OrderType": "2,8,3,6,",
        "OrderStatus": "17",
        "BatchType": 1
    }
    with async_timeout.timeout(REQUEST_TIMEOUT):
        async with session.post(url, json=payload, headers=h) as response:
            r = await response.text()
            click.echo(r)


async def importThirdPartyOrderToXlobo(loop):
    # debug
    access_token = 'ACiYUZ6aKC48faYFD6MpvbOf73BdE9OV5g15q1A6Ghs+i/XIawq/9RHJCzc6Y3UNxA=='
    client_secret = 'APvYM8Mt5Xg1QYvker67VplTPQRx28Qt/XPdY9D7TUhaO3vgFWQ71CRZ/sLZYrn97w=='.lower(
    )
    client_id = '68993573-E38D-4A8A-A263-055C401F9369'
    sql = "select * from stock_order where stock_order.channel_name='京东' and importstatus is null limit 1"
    sessXlobo = aiohttp.ClientSession(loop=loop)
    xloboapi = XloboAPI(sessXlobo, access_token, client_secret, client_id)
    pool = await aiomysql.create_pool(
        host='127.0.0.1',
        port=3306,
        user='root',
        password=db_password,
        db='ymatou',
        charset='utf8mb4',
        loop=loop)
    msg_param = {}
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql)
            r = await cur.fetchone()

            click.echo(r)
            # ((608, '京东', '19810583', '李媛', '河南,郑州,金水区,东风路百脑汇2f09', '100101', '15538072777', None, None, '4901417631381', 3, Decimal('66.33'), '第三方', datetime.datetime(2017, 7, 31, 3, 51, 36), '【日本直邮丨3盒装】Kracie 肌美精 3D超浸透补水深层美白面膜 4枚入 蓝色', None, '待处理', '天狗', None, None, None, None, None, None, None, None, Decimal('199.00'), '410221198404260227', None, None),)
            ai = r[4].split(',')
            productList = [
                {
                    'SkuName': r[14],
                    'SendCountryName': '日本',
                    'SecondLevelCategoryId': 142,
                    'CategoryVersion': '1.0',
                    'Num': r[10],
                    'Weight': 0.3,
                    'UnitPrice': str(r[11]),
                    'Brand': '肌美精',
                    'Specification': '测试'
                },
            ]
            msg_param = {
                'ChannelName': r[1],
                'ChannelUserNickName': '天狗',
                'ChannelUserId': '天狗',
                'OrderCode': r[2],
                'ReceiverName': r[3],
                'ReceiverProvince': ai[0],
                'ReceiverCity': ai[1],
                'ReceiverDistrict': ai[2],
                'ReceiverAddress': ai[3],
                'ReceiverMobile': r[6],
                'ReceiverPostCode': r[5],
                'ReceiverIdCode': r[27],
                'PaymentPrice': str(r[26]),
                'OrderPrice': str(r[26]),
                'ProductList': productList
            }

    result = await xloboapi.importOrder(msg_param)
    click.echo(result)


@click.command()
def importTpoToXlobo():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(importThirdPartyOrderToXlobo(loop))

    # Let's also finish all running tasks:
    pending = asyncio.Task.all_tasks()
    loop.run_until_complete(asyncio.gather(*pending))


@click.command()
def importYmtToXlobo():
    loop = asyncio.get_event_loop()
    sess = aiohttp.ClientSession(loop=loop)
    loop.run_until_complete(importYmtOrderToXlobo(sess, loop))

    # Let's also finish all running tasks:
    pending = asyncio.Task.all_tasks()
    loop.run_until_complete(asyncio.gather(*pending))


@click.command()
def importTGOrder():
    user = 'llw-rb'
    password = '1q2w3e4r5t'

    loop = asyncio.get_event_loop()
    sess = aiohttp.ClientSession(loop=loop)
    tgapi = TiangouAPI(sess, user, password)
    loop.run_until_complete(getTGOrder(tgapi, loop))

    # Let's also finish all running tasks:
    pending = asyncio.Task.all_tasks()
    loop.run_until_complete(asyncio.gather(*pending))


@click.command()
def importCategory():
    access_token = 'AESaZpmFNNcLRbNFmWK38S2ELvpzwjHkRjkpJkNmaaRIpEJ7T+FYBfVvoekui/2k1g=='
    client_secret = 'APvYM8Mt5Xg1QYvker67VplTPQRx28Qt/XPdY9D7TUhaO3vgFWQ71CRZ/sLZYrn97w=='.lower(
    )
    client_id = '8417db83-360c-4275-974f-cf9a2734d8f8'

    loop = asyncio.get_event_loop()
    sess = aiohttp.ClientSession(loop=loop)
    xloboapi = XloboAPI(sess, access_token, client_secret, client_id)
    loop.run_until_complete(getCategory(xloboapi, loop))

    # Let's also finish all running tasks:
    pending = asyncio.Task.all_tasks()
    loop.run_until_complete(asyncio.gather(*pending))


@click.command()
def importLogistic():
    access_token = 'AESaZpmFNNcLRbNFmWK38S2ELvpzwjHkRjkpJkNmaaRIpEJ7T+FYBfVvoekui/2k1g=='
    client_secret = 'APvYM8Mt5Xg1QYvker67VplTPQRx28Qt/XPdY9D7TUhaO3vgFWQ71CRZ/sLZYrn97w=='.lower(
    )
    client_id = '8417db83-360c-4275-974f-cf9a2734d8f8'
    loop = asyncio.get_event_loop()
    sess = aiohttp.ClientSession(loop=loop)
    xloboapi = XloboAPI(sess, access_token, client_secret, client_id)
    loop.run_until_complete(xloboapi.getLogistic())

    # Let's also finish all running tasks:
    pending = asyncio.Task.all_tasks()
    loop.run_until_complete(asyncio.gather(*pending))


@click.command()
def importLogisticCompany():
    appid = 'llzlHWWDTkEsUUjwKf'
    appsecret = 'xdP5yraJQdpypKZNQ0M0zqE35dcrEWox'
    authcode = 'Ul1BpFlBHdLR6EnEv75RV6QeradgjdBk'
    loop = asyncio.get_event_loop()
    sessYmt = aiohttp.ClientSession(
        loop=loop, headers={'Content-Type': 'application/json'})
    ymtapi = YmatouAPI(sessYmt, appid, appsecret, authcode)
    result = loop.run_until_complete(ymtapi.getLogisticCompany())

    # Let's also finish all running tasks:
    pending = asyncio.Task.all_tasks()
    loop.run_until_complete(asyncio.gather(*pending))
    print(result)


@click.command()
def importProduct():
    loop = asyncio.get_event_loop()
    # breaks because of the first url
    url = 'http://www.xlobo.com/api/ProductApi/QueryProduct'
    payloads = [{
        'PageNumber': str(i),
        'PageSize': '200'
    } for i in range(19, 20)]
    headers = {
        'Cookie':
        '__jsluid=4e7aeb4f3ba79bb7b61a4823504c623c; IESESSION=alive; pgv_pvi=8676397056; pgv_si=s7894683648; tencentSig=1717213184; ASP.NET_SessionId=bf1fzanbw4sbevr3ltfwlbt3; _qddaz=QD.k9ubom.45d3b.iyvg35iy; xlobo-page-lang=lang=PageResource; _qddab=3-2jkp70.j5pe9izt; login=true; .AUTH4BUYER=D595FCA17AB87A5C1D92C768E439F3D78CCB04CDAC758F30617B0356BB864F2FFA996F640A527D9CE5AD6C8D518365198B2AE5E9B66F74AB861C65C18109A0F4F9958118B2CE56AB0321A2B3ECEA80E327EFCA6A5808B09928F342BC982A6EE59AEC50F11D7A478332C356039C7C216380D036A0; _xlobotoken=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJVc2VySWQiOiJhNzhhMmE4ZC0wNDAwLTRiOTMtYjk1My1kYjY3Y2U3ZTUwZDEiLCJVc2VyTmFtZSI6IuS4nOS6rOW9qeiZueahpSIsIkNvdW50cnlJZCI6NiwiQ2VydFR5cGUiOjEsIlZpcCI6MiwiQ2VydENvdW50cnlJZCI6NiwiUHJlVGF4U3RhdHVzIjowfQ.b5nz5b6hcELc5cC3QTje4Y6EeuyrFE2QWIEO9blTSvs; __utmt=1; __utma=157028338.1662092929.1499179608.1501366814.1501464646.10; __utmb=157028338.1.10.1501464646; __utmc=157028338; __utmz=157028338.1501464646.10.9.utmcsr=my.xlobo.com|utmccn=(referral)|utmcmd=referral|utmcct=/mybeihai/index.aspx; _ga=GA1.2.1662092929.1499179608; _gid=GA1.2.1882234136.1501464598',
        'Content-Type':
        'application/json;charset=UTF-8',
        'Accept':
        'application/json, text/plain, */*',
        'Referer':
        'http://www.xlobo.com/product/productlist',
        'Pragma':
        'no-cache',
        'Origin':
        'http://www.xlobo.com',
        'Accept-Encoding':
        'gzip, deflate',
        'Accept-Language':
        'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4',
        'User-Agent':
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
        'Cache-Control':
        'no-cache'
    }

    with aiohttp.ClientSession(loop=loop, headers=headers) as session:
        loop.run_until_complete(fetch_all(session, url, payloads, loop))


@click.command()
def exportStock():
    conn = pymysql.connect(
        user='root',
        host='127.0.0.1',
        passwd=db_password,
        db='ymatou',
        # http://stackoverflow.com/questions/2108824/mysql-incorrect-string-value-error-when-save-unicode-string-in-django
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor)
    syncstock = SyncStock()
    xloboStock = syncstock.syncXloboStockByGoogle()
    gzStock = syncstock.syncGzStockByGoogle()

    querySql = 'select id from stock_product where jancode=%s'
    updateSql = 'update stock_stock set quantity=%s where jancode=%s'
    try:
        with conn.cursor() as cursor:
            for i in list(syncstock.chunks(xloboStock, 3)):
                cursor.execute(querySql, (i[0]))
            #     cursor.executemany(
            #         updateSql,
            #         (i[2], i[0]), )  # (jancode, prodcut_name, quantity)
            # conn.commit()
    finally:
        conn.close()


@click.group()
def cli():
    pass


# @click.command()
# @click.option('--filename', help='excel file')
# def importProduct(filename):
#     click.echo('Initialized the database')
#     import_data = Dataset().load(open(filename).read())
#     click.echo(import_data)
cli.add_command(importTGOrder)
cli.add_command(importProduct)
cli.add_command(importCategory)
cli.add_command(importLogistic)
cli.add_command(importTpoToXlobo)
cli.add_command(importYmtToXlobo)
cli.add_command(exportStock)
cli.add_command(importLogisticCompany)

if __name__ == '__main__':
    cli()
