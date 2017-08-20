import async_timeout

REQUEST_TIMEOUT = 30


class UexAPI():
    def __init__(self, session, user, password):
        self.user = user
        self.password = password
        self.session = session

    async def login(self):
        url = 'http://www.uex.co.jp/Home/User/login.html'
        payload = {'username': self.user, 'password': self.password}

        with async_timeout.timeout(REQUEST_TIMEOUT):
            async with self.session.post(url, data=payload) as response:
                return await response.json()

    # goods[0][jan_code]:4582138096408
    # goods[0][num]:2
    # add_server[0]:1
    # ship_id:24
    # user_order_no:12345678
    # address[consignee]:李春
    # address[phone]:13811272817
    # address[province]:北京
    # address[city]:北京
    # address[district]:朝阳
    # address[street]:
    # address[address]:北苑路222号
    # address[card]:352525199012282165
    # send_user:天狗
    # send_user_phone:17382827171
    # send_user_address:东京
    # {"code": 1, "msg": "成功", "order_sn": "UEXE170810012"} error: {"code":0, "msg":"错误信息"}
    async def stockOut(self, payload):
        url = 'http://www.uex.co.jp/skuuser/outstock/add'
        with async_timeout.timeout(REQUEST_TIMEOUT):
            async with self.session.post(url, data=payload) as response:
                return await response.text()
