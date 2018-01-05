from django.test import TestCase

from ymatou.gmail import GmailScraper


class GmailScraperTestCase(TestCase):
    def test_process_mail(self):
        gsApi = GmailScraper('rainbowtokyorainbowtokyo@gmail.com',
                             'rainbow123')
        gsApi.login()
        pos = [
            # {
            #     'orderid': '244562-20171128-00516718',
            #     'name': 'rakuten',
            #     'delivery_no': None,
            #     'payment': None
            # },
            # {
            #     'orderid': '265611-20171120-00937802',
            #     'name': 'rakuten',
            #     'delivery_no': None,
            #     'payment': None,
            # },
            # {
            #     'orderid': '206504-20171120-01448812',
            #     'name': 'rakuten',
            #     'delivery_no': None,
            #     'payment': None,
            # },
            # {
            #     'orderid': '253260-20171120-00061801',
            #     'name': 'rakuten',
            #     'delivery_no': None,
            #     'payment': None,
            # },
            # {
            #     'orderid': '203677-20171129-013958715',
            #     'name': 'rakuten',
            #     'delivery_no': None,
            #     'payment': None,
            # },
            # {
            #     'orderid': '20171118-00203822',
            #     'name': 'rakuten',
            #     'delivery_no': None,
            #     'payment': None,
            # },
            # {
            #     'orderid': 'Y000000033193640',
            #     'name': 'rakuten',
            #     'delivery_no': None,
            #     'payment': None,
            # },
            # {
            #     'orderid': '068-g000335448-i01',
            #     'name': 'rakuten',
            #     'delivery_no': None,
            #     'payment': None,
            # },
            # {
            #     'orderid': '20171207000000741',
            #     'name': 'rakuten',
            #     'delivery_no': None,
            #     'payment': None,
            # },
            # {
            #     'orderid': '503-3006255-9574205',
            #     'name': 'Amazon',
            #     'delivery_no': None,
            #     'payment': None,
            # },
            # {
            #     'orderid': '503-3100187-7108622',
            #     'name': 'Amazon',
            #     'delivery_no': None,
            #     'payment': None,
            # },
            # {
            #     'orderid': '503-2349801-1892618',
            #     'name': 'Amazon',
            #     'delivery_no': None,
            #     'payment': None,
            # },
            # {
            #     'orderid': '395877948,',
            #     'name': 'Rakuten',
            #     'delivery_no': None,
            #     'payment': None,
            # },
            {
                'orderid': '3351325',
                'name': 'Rakuten',
                'delivery_no': None,
                'payment': None,
            },
            {
                'orderid': '2018010300489',
                'name': 'Rakuten',
                'delivery_no': None,
                'payment': None,
            },
        ]
        for po in pos:
            deliveryNos, payment = gsApi.processMailbox(po)
            print(deliveryNos, payment)
        self.assertEqual('ok', 'ok')
