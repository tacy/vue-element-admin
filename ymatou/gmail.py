import email
import imaplib
import logging
import os.path
import re
import sys
import pymysql

logger = logging.getLogger(__name__)


class GmailScraper():
    def __init__(self, emailAccount, passwd):
        self.emailAccount = emailAccount
        self.passwd = passwd

    def login(self):
        self.mailbox = imaplib.IMAP4_SSL('imap.gmail.com')
        try:
            rv, data = self.mailbox.login(self.emailAccount, self.passwd)
        except imaplib.IMAP4.error as e:
            logger.exception("LOGIN FAILED!!! ")
            sys.exit(1)
        self.mailbox.select('"[Gmail]/All Mail"')

    def processMailbox(self, purchaseorder):
        """
        Do something with emails messages in the folder.
        For the sake of this example, print some headers.
        """
        orderid = purchaseorder['orderid']
        supplier = purchaseorder['name']
        deliveryNos = purchaseorder['delivery_no'].split(',') if purchaseorder[
            'delivery_no'] else []

        # http://www.4d.com/docs/CMU/CMU88864.HTM
        searchKey = {
            'Amazon': ('BODY', orderid, 'FROM',
                       'shipment-tracking@amazon.co.jp'),
            'Rakuten': ('BODY', orderid),
        }
        if supplier != 'Amazon': supplier = 'Rakuten'
        rv, data = self.mailbox.search(None, *searchKey[supplier])
        if rv != 'OK':
            logger.warning("No purchase:[%s] found!", orderid)
            return []
        logger.info('purchaseorder: %s, search result: %s', orderid, data[0])

        payment = purchaseorder['payment'] if purchaseorder['payment'] else 0
        for num in data[0].split():
            rv, data = self.mailbox.fetch(num, '(RFC822)')
            if rv != 'OK':
                logger.warning("ERROR getting message, purchase: %s, mail: %s",
                               orderid, num)
                continue
            msg = email.message_from_bytes(data[0][1])
            if supplier == 'Amazon':
                ds, payment2 = self.amazon(msg)
                # 存在分拆发货的情况, 需要累加payment
                if (ds and ds[0] not in deliveryNos) or (not ds and payment2):
                    payment += float(payment2.replace(',', ''))
                deliveryNos.extend(ds)
            else:
                ds, payment2 = self.rakuten(msg, payment)
                if not payment and payment2:
                    payment = float(payment2.replace(',', ''))
                deliveryNos.extend(ds)

            # https://stackoverflow.com/questions/1463074/how-can-i-get-an-email-messages-text-content-using-python
            # https://stackoverflow.com/questions/38970760/how-to-decode-a-mime-part-of-a-message-and-get-a-unicode-string-in-python-2

        dedup_deliveryNos = list(set(deliveryNos))
        if dedup_deliveryNos:
            logger.info('purchaseorder: %s, delivery_nos: %s', orderid,
                        str(dedup_deliveryNos))
        if payment:
            logger.info('purchaseorder: %s, payment amount: %s', orderid,
                        payment)
        return (dedup_deliveryNos, payment)

    def amazon(self, msg, payment=None):
        result = []
        for part in msg.walk():
            # multipart are just containers, so we skip them
            if part.get_content_type() == 'text/html':
                part_charset = part.get_content_charset()
                html = part.get_payload(decode=True).decode(
                    part_charset, 'replace')
                if not result:
                    match = re.search(r'伝票番号は([0-9\-].*?)です', html)
                    if match:
                        result.append(match.group(1))
                        match = re.search(
                            r'(?:クレジットカード|合計).*\r?\n?.*?￥\s+([\d,]{3,})', html)
                        payment = match.group(1)
                        break
                    else:  # 亚马逊有些第三方订单没有返回运单号
                        match = re.search(
                            r'(?:クレジットカード|合計).*\r?\n?.*?￥\s+([\d,]{3,})', html)
                        if match:
                            payment = match.group(1)
        return (result, payment)

    def rakuten(self, msg, payment):
        result = []
        for part in msg.walk():
            # multipart are just containers, so we skip them
            if part.get_content_type() in ['text/plain', 'text/html']:
                part_charset = part.get_content_charset()
                html = part.get_payload(decode=True).decode(
                    part_charset, 'replace')
                if not result:
                    match = re.search(
                        r'(?:(?:配送会社お)?問い?合わ?せ番号|伝票番号(?:.*?\r\n)?|宅配伝票No|送り状No|reqCodeNo1).*?(\d{5,})',
                        html)
                    if match:
                        result.append(match.group(1))
                if not payment:
                    match = re.search(r'合計.*?([\d,]{3,})', html)
                    if match:
                        payment = match.group(1)
        return (result, payment)


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
    gsApi = GmailScraper('rainbowtokyorainbowtokyo@gmail.com', 'rainbow123')
    gsApi.login()
    # pos = [
    #     # {
    #     #     'orderid': '244562-20171128-00516718',
    #     #     'name': 'rakuten',
    #     #     'delivery_no': None,
    #     #     'payment': None
    #     # },
    #     # {
    #     #     'orderid': '265611-20171120-00937802',
    #     #     'name': 'rakuten',
    #     #     'delivery_no': None,
    #     #     'payment': None,
    #     # },
    #     # {
    #     #     'orderid': '206504-20171120-01448812',
    #     #     'name': 'rakuten',
    #     #     'delivery_no': None,
    #     #     'payment': None,
    #     # },
    #     # {
    #     #     'orderid': '253260-20171120-00061801',
    #     #     'name': 'rakuten',
    #     #     'delivery_no': None,
    #     #     'payment': None,
    #     # },
    #     # {
    #     #     'orderid': '203677-20171129-013958715',
    #     #     'name': 'rakuten',
    #     #     'delivery_no': None,
    #     #     'payment': None,
    #     # },
    #     # {
    #     #     'orderid': '20171118-00203822',
    #     #     'name': 'rakuten',
    #     #     'delivery_no': None,
    #     #     'payment': None,
    #     # },
    #     # {
    #     #     'orderid': 'Y000000033193640',
    #     #     'name': 'rakuten',
    #     #     'delivery_no': None,
    #     #     'payment': None,
    #     # },
    #     # {
    #     #     'orderid': '068-g000335448-i01',
    #     #     'name': 'rakuten',
    #     #     'delivery_no': None,
    #     #     'payment': None,
    #     # },
    #     # {
    #     #     'orderid': '20171207000000741',
    #     #     'name': 'rakuten',
    #     #     'delivery_no': None,
    #     #     'payment': None,
    #     # },
    #     # {
    #     #     'orderid': '503-3006255-9574205',
    #     #     'name': 'Amazon',
    #     #     'delivery_no': None,
    #     #     'payment': None,
    #     # },
    #     # {
    #     #     'orderid': '503-3100187-7108622',
    #     #     'name': 'Amazon',
    #     #     'delivery_no': None,
    #     #     'payment': None,
    #     # },
    #     {
    #         'orderid': '503-2349801-1892618',
    #         'name': 'Amazon',
    #         'delivery_no': None,
    #         'payment': None,
    #     },
    # ]
    # for po in pos:
    #     deliveryNos, payment = gsApi.processMailbox(po)
    #     print(deliveryNos, payment)

    query_sql = 'select po.orderid, s.name, po.delivery_no, po.id, po.payment from stock_purchaseorder po inner join stock_supplier s on po.supplier_id=s.id where po.status in ("在途中", "入库中") and s.name in ("Amazon", "Rakuten", "产品官网", "Lohaco")'
    update_sql = 'update stock_purchaseorder set delivery_no=%s,payment=%s where id=%s'

    connection = pymysql.connect(
        host='127.0.0.1',
        user='root',
        password='asd12288',
        db='ymatou',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor)

    with connection.cursor() as cursor:
        cursor.execute(query_sql)
        result = cursor.fetchall()
        for r in result:
            logger.info('purchaseorder: %s', str(r))
            deliverys, payment = gsApi.processMailbox(r)
            delivery_no = ','.join(deliverys)
            if delivery_no != r['delivery_no'] or payment != r['payment']:
                cursor.execute(update_sql, (delivery_no, payment, r['id']))
                connection.commit()
