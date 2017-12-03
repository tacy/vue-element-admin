import email
import email.header
import imaplib
import logging
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
        searchKey = {
            'Amazon': ('BODY', orderid, 'FROM',
                       'shipment-tracking@amazon.co.jp'),
            'Rakuten': ('BODY', orderid),
        }
        rv, data = self.mailbox.search(None, *searchKey[supplier])
        if rv != 'OK':
            logger.warning("No purchase:[%s] found!" % (orderid))
            return []
        logger.info('purchaseorder', orderid, 'search result:', data[0])

        for num in data[0].split():
            rv, data = self.mailbox.fetch(num, '(RFC822)')
            if rv != 'OK':
                logger.warning("ERROR getting message, purchase: %s" %
                               (orderid))
                continue
            msg = email.message_from_bytes(data[0][1])

            # https://stackoverflow.com/questions/1463074/how-can-i-get-an-email-messages-text-content-using-python
            # https://stackoverflow.com/questions/38970760/how-to-decode-a-mime-part-of-a-message-and-get-a-unicode-string-in-python-2
            for part in msg.walk():
                # multipart are just containers, so we skip them
                if part.get_content_type() in ['text/plain',
                                               'text/html']:  # text/html
                    part_charset = part.get_content_charset()
                    html = part.get_payload(decode=True).decode(part_charset)
                    match = None
                    if supplier == 'Amazon':
                        match = re.search(r'伝票番号は([0-9\-].*)です', html)
                    else:
                        match = re.search(r'伝票番号.+?([0-9-]+)', html)
                    if match:
                        deliveryNos.append(match.group(1))
                        break
        return list(set(deliveryNos))


if __name__ == '__main__':
    gsApi = GmailScraper('rainbowtokyorainbowtokyo@gmail.com', 'rainbow123')
    gsApi.login()
    # po = {
    #     'orderid': '244562-20171128-00516718',
    #     'supplier': 'rakuten',
    #     'delivery_no': None
    # }
    # po = {
    #     'orderid': '503-8437358-7411017',
    #     'supplier': 'amazon',
    #     'delivery_no': None
    # }
    # deliveryNos = gsApi.processMailbox(po)
    # print(deliveryNos)
    query_sql = 'select po.orderid, s.name, po.delivery_no, po.id from stock_purchaseorder po inner join stock_supplier s on po.supplier_id=s.id where po.status in ("在途中", "入库中") and s.name in ("Amazon", "Rakuten")'
    update_sql = 'update stock_purchaseorder set delivery_no=%s where id=%s'

    connection = pymysql.connect(
        host='127.0.0.1',
        user='root',
        password='12345678',
        db='ymatou',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor)

    with connection.cursor() as cursor:
        cursor.execute(query_sql)
        result = cursor.fetchall()
        for r in result:
            print(r)
            delivery_no = ','.join(gsApi.processMailbox(r))

            if delivery_no != r['delivery_no']:
                cursor.execute(update_sql, (delivery_no, r['id']))
                connection.commit()
