import os
import logging
import eventlet
import gspread

from io import BytesIO
# from oauth2client.client import SignedJwtAssertionCredentials
from oauth2client.service_account import ServiceAccountCredentials
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm, inch
from reportlab.pdfbase import pdfmetrics, ttfonts
from reportlab.graphics.barcode import createBarcodeDrawing
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle

log = logging.getLogger(__name__)


class PDFTool:
    def __init__(self):
        pdfmetrics.registerFont(
            ttfonts.TTFont(
                'wqy', '/usr/share/fonts/wenquanyi/wqy-zenhei/wqy-zenhei.ttc'))

    def createShippingPDF(self, db_number, orders):
        styles = getSampleStyleSheet()
        buf = BytesIO()

        doc = SimpleDocTemplate(
            buf,
            rightMargin=2,
            leftMargin=2,
            topMargin=2,
            bottomMargin=2,
            pagesize=(10 * cm, 15 * cm))
        elements = []
        # title = 'DB Number: {}'.format(db_number)
        # elements.append(Paragraph(title, styles['h5']))
        barcode = createBarcodeDrawing(
            'Code128',
            value=db_number,
            humanReadable=True,
            barWidth=0.015 * inch)
        elements.append(barcode)

        data = [
            ['产品', '规格', '数量', '位置'],
            # [
            #     Paragraph('<font name="aa">超值产品牛步哈哈确实不错45ETTECADDD</font>',
            #               styles['Normal']), '11', '12', 'A1B1104'
            # ],
        ]
        for o in orders:
            prodname = '<font name="wqy">{}/{}</font>'.format(
                o[0].replace(' ', ','), o[5]
                if not o[5] else o[5].replace(' ', ','))
            sku_properties_name = '<font name="wqy">{}/{}</font>'.format(
                o[1].replace(' ', ','), o[2])
            location = '<font name="wqy">{}</font>'.format(o[4])
            data.append([
                Paragraph(prodname, styles['Normal']),
                Paragraph(sku_properties_name, styles['Normal']),
                o[3],
                # o[4],
                Paragraph(location, styles['Normal'])
            ])
        t = Table(
            data,
            colWidths=[
                4.5 * cm,
                2.8 * cm,
                1.0 * cm,
                1.4 * cm,
            ],
        )
        t.setStyle(
            TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'wqy'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
            ]))
        elements.append(t)
        doc.build(elements)
        pdf = buf.getvalue()
        buf.close()
        return pdf


class GoogleSpread:
    def __init(self):
        self.doc = None

    def open_google_doc(self, doc_name):
        cdir = os.path.dirname(os.path.abspath(__file__))
        json_key = os.path.join(cdir, 'tacy-speedsheet-d32988f60e38.json')
        scope = ['https://spreadsheets.google.com/feeds']

        # credentials = SignedJwtAssertionCredentials(
        #     json_key['client_email'], json_key['private_key'], scope)
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            json_key, scope)
        try:
            with eventlet.Timeout(120):
                gc = gspread.authorize(credentials)
                self.doc = gc.open(doc_name)
        except (Exception, eventlet.Timeout):
            log.exception('Open google doc failed')
            raise

    def read_google_doc_by_col(self, wks_name, col):
        wks = self.doc.worksheet(wks_name)
        return wks.col_values(col)

    def read_google_doc_by_range(self, wks_name, rangestr, all_rows=False):
        wks = self.doc.worksheet(wks_name)
        if all_rows:
            count = wks.row_count
            rangestr = rangestr + str(count)
        r = wks.range(rangestr)
        return [i.value for i in r]

    def write_google_doc(self, wks_name, data, size, mode, left, right):
        c_range = None
        wks = self.doc.worksheet(wks_name)
        orc = wks.row_count

        try:
            with eventlet.Timeout(120):
                if 'append' in mode:
                    wks.add_rows(size)
                    rc = wks.row_count
                    c_range = left + str(orc + 1) + ':' + right + str(rc)
                else:
                    c_range = left + '2:' + right + str(size)
                    wks.resize(size)  # overwrite all cell
                log.info(c_range)

                cells = wks.range(c_range)
                for cell, value in zip(cells, data):
                    cell.value = value
                wks.update_cells(cells)
        except (Exception, eventlet.Timeout):
            log.exception('Write google doc failed')
            raise

    def chunks(self, arrays, size):
        for i in range(0, len(arrays), size):
            yield arrays[i:i + size]


# class SyncStock:
#     def __init__(self):
#         pass

#     def chunks(self, arrays, size):
#         """Yield successive n-sized chunks from l."""
#         for i in range(0, len(arrays), size):
#             yield arrays[i:i + size]

#     def syncXloboStockByGoogle(self):
#         ss = gsp.open_google_doc('virtualstock-products')
#         stocks = gsp.read_google_doc_by_range(
#             ss, 'stock', 'A2:C', all_rows=True)
#         return stocks

#     def syncGzStockByGoogle(self):
#         ss = gsp.open_google_doc(u'国内库存出入库流水.xls')
#         stocks = gsp.read_google_doc_by_range(
#             ss, '最新表入库', 'A2:C', all_rows=True)
#         return stocks
