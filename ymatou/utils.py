from io import BytesIO

from reportlab.lib import colors, pagesizes
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics, ttfonts
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle


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
            pagesize=pagesizes.A6)
        elements = []
        title = 'DB Number: {}'.format(db_number)
        elements.append(Paragraph(title, styles['title']))

        data = [
            ['产品', '规格', '数量', '位置'],
            # [
            #     Paragraph('<font name="aa">超值产品牛步哈哈确实不错45ETTECADDD</font>',
            #               styles['Normal']), '11', '12', 'A1B1104'
            # ],
        ]
        for o in orders:
            print(o)
            prodname = '<font name="wqy">{}</font>'.format(
                o[0].replace(' ', ','))
            sku_properties_name = '<font name="wqy">{}</font>'.format(
                o[1].replace(' ', ','))
            data.append([
                Paragraph(prodname, styles['Normal']),
                Paragraph(sku_properties_name, styles['Normal']),
                o[2],
                o[3],
            ])
        t = Table(
            data,
            colWidths=[
                4.5 * cm,
                2.8 * cm,
                1.0 * cm,
                1.8 * cm,
            ], )
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
