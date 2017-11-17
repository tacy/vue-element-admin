import os.path
import random
import re
import logging
import arrow
import requests
from django.conf import settings

logging = logging.getLogger(__name__)


def getJapanEMSStorageLocal():
    return settings.EMS_STORAGE_DIR


class JapanEmsAPI():
    def __init__(self, user, password):
        self.urltpl = 'https://www.int-mypage.post.japanpost.jp/mypage/'
        self.user = user
        self.password = password
        self.sess = requests.Session()
        self.sess.headers.update({
            'User-Agent':
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
            'Content-Type':
            'application/x-www-form-urlencoded',
        })

    def login(self):
        url = self.urltpl + 'M010000.do'
        self.sess.get(url)
        payload = {
            'method:login': '',
            'request_locale': 'zh',
            'localeSel': 'zh',
            'loginBean.id': self.user,
            'loginBean.pw': self.password,
        }
        self.sess.post(url, data=payload)

    def call(self, urlsuf, payload):
        url = self.urltpl + urlsuf
        result = self.sess.post(url, payload)
        return result


# 生成日本邮政EMS面单
def createJapanEMS(orderInfo,
                   sendType,
                   transType=None,
                   storagePath=None,
                   country='CN'):
    # sendType
    #    EMS(物品): 1 / 国际e包裹: 4 / 国际邮包: 5
    # transType
    #    航空: 1 / 标准航空(SAL): 3 / 海运: 2
    # pkgType
    #    Gift: 0 / Document: 1/ Sample: 2 / Merchandise: 3 / Personal Effects: 4 / Others: 5
    # senderInstruction(国际邮包退运)
    #    Return to origin immediately: 1 / Return to sender after specified period:2 / Redirect: 3 / Treat as abandoned: 4
    # fwTransType(退运方式)
    #    AIR: 1 / by surface/SAL: 4
    #
    jemsAPI = JapanEmsAPI('rainbowtokyorainbowtokyo@gmail.com', 'shining123')
    jemsAPI.login()
    ems_date = arrow.now()
    addrSplit = orderInfo['receiver_address'].split(',')

    # epack赔付最高6000日元, ems包裹赔付20000日元
    price = random.randint(19000, 20000)
    if sendType == 4:
        price = random.randint(5500, 6000)

    # 1. 做单
    payload = {
        'method:onlineS': '',
        'request_locale': 'zh',
        'sx': 0,
        'sy': 0,
        'calendarBean.selIndex': '',
        'calendarBean.dispYmdBean.year': ems_date.format('YYYY'),
        'calendarBean.dispYmdBean.month': ems_date.format('MM'),
        'calendarBean.dispYmdBean.day': ems_date.format('DD'),
    }
    jemsAPI.call('M010100.do', payload)

    # 2.寄件人登入
    payload = {
        'method:regist': '',
        'addrFromBean.courierFlg': 0,
        'addrFromBean.nam': 'DONGJINGCANG KAEI',
        'addrFromBean.companyName': '',
        'addrFromBean.postName': '',
        'addrFromBean.hojo1': '',
        'addrFromBean.hojo2': '',
        'addrFromBean.mail': '',
        'addrFromBean.postal': '1770045',
        'addrFromBean.add1': '',
        'addrFromBean.add2': 'TOKYO NERIMA SHAKUJIIDAI 3-9-18 DONGJINGCANG',
        'addrFromBean.add3': 'NERIMA',
        'addrFromBean.pref': 'Tokyo',
        'addrFromBean.tel': '08030097238',
        'addrFromBean.fax': '',
        'addrFromBean.exportCd': '',
        'addrFromBean.initDisp': '0',
    }
    jemsAPI.call('M060105.do', payload)

    # 3. 收件人登入
    add2 = addrSplit[3] if country == 'CN' else orderInfo['receiver_address']
    add3 = ','.join(addrSplit[1:3]) if country == 'CN' else addrSplit[1]
    addPref = addrSplit[0] if country == 'CN' else addrSplit[2]
    payload = {
        'method:regist': '',
        'addrToBean.courierFlg': '0',
        'addrToBean.nam': orderInfo['receiver_name'],
        'addrToBean.companyName': '',
        'addrToBean.postName': '',
        'addrToBean.couCode': country,
        'addrToBean.sortNum': 1,
        'addrToBean.add1': '',
        # 'addrToBean.add2': addrSplit[3],
        # 'addrToBean.add3': ','.join(addrSplit[1:3]),
        # 'addrToBean.pref': addrSplit[0],
        'addrToBean.add2': add2,
        'addrToBean.add3': add3,
        'addrToBean.pref': addPref,
        'addrToBean.postal': orderInfo['receiver_zip'],
        'addrToBean.tel': orderInfo['receiver_mobile'],
        'addrToBean.fax': '',
        'addrToBean.mail': '',
    }
    jemsAPI.call('M060505.do', payload)

    # 4. 内容物品登录
    payload = {
        'method:itemAdd': '',
        'cdSel': '',
        'shippingBean.overConfirm': '',
        'janCd': '',
        'shippingBean.sendType': 1,
        'shippingBean.pkgType': 0,
        'shippingBean.pkgTotalPrice.value': '',
        'shippingBean.curUnit': 'JPY',
        '__checkbox_shippingBean.noCm': 'true',
        '__checkbox_ShippingBean.danger': 'true',
    }
    if transType:
        payload['shippingBean.transType'] = transType
    jemsAPI.call('M060800.do', payload)

    # 5. 注册商品内容
    prod_name = '_'.join(
        ['SUPPLYMENT', orderInfo['jancode'][1:], orderInfo['orderid']])
    payload = {
        'method:regist': '',
        'itemBean.pkg': prod_name,
        'itemBean.hsCode': '',
        'itemBean.couCd': '',
        'itemBean.weight.value': '',
        'itemBean.cost.value': price,
        'itemBean.curUnit': 'JPY',
    }
    jemsAPI.call('M080100.do', payload)

    # 6. 添加商品到列表
    payload = {
        'method:update': '',
    }
    jemsAPI.call('M080101.do', payload)

    # 7. 登入物品提交
    payload = {
        'method:regist': '',
        'cdSel': '',
        'shippingBean.overConfirm': '',
        'janCd': '',
        'shippingBean.sendType': sendType,
        'cost.value': price,
        'curUnit': 'JPY',
        'curUnitEtc': '',
        'printCurUnit': 'JPY',
        'itemCount': 1,
        'shippingBean.pkgType': 0,
        'shippingBean.pkgTotalPrice.value': price,
        'shippingBean.curUnit': 'JPY',
        '__checkbox_shippingBean.noCm': 'true',
        'ShippingBean.danger': 'true',
        '__checkbox_ShippingBean.danger': 'true',
    }
    if transType:
        payload['shippingBean.transType'] = transType
    jemsAPI.call('M060800.do', payload)

    # 7.1 如果是国际邮包, 需要设置退运方式
    if transType:
        payload = {
            'method:regist': '',
            'cdSel': '',
            'shippingBean.senderInstruction': 2,
            'shippingBean.retentionDays.value': 30,
            'shippingBean.fwTransType': 4,
        }
        jemsAPI.call('M060910.do', payload)

    # 8. 确认面单信息
    payload = {
        'method:regist': '',
        'emsNo.value': 1,
        'shippingBean.sendDate.YMD': ems_date.format('YYYY/MM/DD'),
        'shippingBean.num.value': '',
        'shippingBean.totalNum.value': '',
        'shippingBean.totalWeight.value': '',
        'shippingBean.cost.value': '',
        'shippingBean.damges': '',
        'shippingBean.insure.value': '',
        'shippingBean.invPrintType': 0,
        'shippingBean.invPrintNum.value': 1,
        'shippingBean.licenceNum': '',
        'shippingBean.certNum': '',
        'shippingBean.invoiceNum': '',
        'shippingBean.taxCode': '',
        'shippingBean.payCond': '',
        'shippingBean.invBiko': '',
        '__checkbox_shippingBean.ctrlMailConfBean.fromConf1': 'true',
        '__checkbox_shippingBean.ctrlMailConfBean.fromConf3': 'true',
        '__checkbox_shippingBean.ctrlMailConfBean.fromConf4': 'true',
        '__checkbox_shippingBean.ctrlMailConfBean.fromConf5': 'true',
        '__checkbox_shippingBean.ctrlMailConfBean.fromConf6': 'true',
        '__checkbox_shippingBean.ctrlMailConfBean.fromConf2': 'true',
        '__checkbox_shippingBean.ctrlMailConfBean.fromConf7': 'true',
        '__checkbox_shippingBean.ctrlMailConfBean.toConf1': 'true',
        '__checkbox_shippingBean.ctrlMailConfBean.toConf3': 'true',
        '__checkbox_shippingBean.ctrlMailConfBean.toConf4': 'true',
        '__checkbox_shippingBean.ctrlMailConfBean.toConf5': 'true',
        '__checkbox_shippingBean.ctrlMailConfBean.toConf6': 'true',
        '__checkbox_shippingBean.ctrlMailConfBean.toConf2': 'true',
        '__checkbox_shippingBean.ctrlMailConfBean.toConf7': 'true',
    }
    if transType:
        payload.update({
            '__checkbox_shippingBean.withInsurance': 'true',
            '__checkbox_shippingBean.adviceOfDelivery': 'true',
            'shippingBean.senderInstruction': 2,
        })
    jemsAPI.call('M060900.do', payload)

    # 9. 发送面单
    payload = {
        'method:regist': '',
    }
    jemsAPI.call('M061000.do', payload)

    # 10. 打印面单
    payload = {
        'method:print': '',
    }
    r = jemsAPI.call('M061100.do', payload)

    match = re.search(r'<iframe src="(.*?)"', r.text)
    urlsuf = match.group(1)
    ems_number = urlsuf.split('=')[1][14:27]
    pdfurl = jemsAPI.urltpl + urlsuf
    r = jemsAPI.sess.get(pdfurl)
    if not storagePath:
        storagePath = getJapanEMSStorageLocal()
    fileName = os.path.join(storagePath, ems_number + '.pdf')
    logging.debug(
        'japanemsAPI: pdfurl: {}, ems_number: {}, fileName: {}'.format(
            pdfurl, ems_number, fileName))

    with open(fileName, 'wb') as f:
        f.write(r.content)

    return ems_number


# sendType  EMS(物品): 1 / 国际e包裹: 4 / 国际邮包: 5  | transType 航空: 1 / 标准航空(SAL): 3 / 海运: 2
if __name__ == '__main__':
    orderinfo = {
        'receiver_name': 'lichunlong',
        'receiver_address': '168-22 Powell Cove Blvd #9, Beechhurst, NY',
        'receiver_zip': '100000',
        'receiver_mobile': '12922929192',
        'jancode': '4383829292',
        'orderid': '12233333',
    }
    createJapanEMS(
        orderinfo,
        5,
        2,
        country='US',
        storagePath='/home/tacy/workspace/python/lelewu/emspdfs')
