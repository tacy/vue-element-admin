# from io import BytesIO
from reportlab.lib.units import cm
from reportlab.lib import colors, pagesizes
from reportlab.pdfbase import pdfmetrics, ttfonts
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph

pdfmetrics.registerFont(
    ttfonts.TTFont('aa',
                   '/usr/share/fonts/wenquanyi/wqy-zenhei/wqy-zenhei.ttc'))
styles = getSampleStyleSheet()
doc = SimpleDocTemplate(
    "simple_table.pdf",
    rightMargin=2,
    leftMargin=2,
    topMargin=2,
    bottomMargin=2,
    pagesize=pagesizes.A6)
elements = []
elements.append(Paragraph("DB Number: DB1122929292", styles['title']))

data = [
    ['产品', '规格', '数量', '位置'],
    [
        Paragraph('<font name="aa">超值产品牛步哈哈确实不错45ETTECADDD</font>',
                  styles['Normal']), '11', '12', 'A1B1104'
    ],
    [
        Paragraph('<font name="aa">超值产品牛步哈哈确实不错45ETTECADDD</font>',
                  styles['Normal']), '11', '12', 'A1B1104'
    ],
    [
        Paragraph('<font name="aa">超值产品牛步哈哈确实不错45ETTECADDD</font>',
                  styles['Normal']), '11', '12', 'A1B1104'
    ],
    [
        Paragraph('<font name="aa">超值产品牛步哈哈确实不错45ETTECADDD</font>',
                  styles['Normal']), '11', '12', 'A1B1104'
    ],
    [
        Paragraph('<font name="aa">超值产品牛步哈哈确实不错45ETTECADDD</font>',
                  styles['Normal']), '11', '12', 'A1B1104'
    ],
    [
        Paragraph('<font name="aa">超值产品牛步哈哈确实不错45ETTECADDD</font>',
                  styles['Normal']), '11', '12', 'A1B1104'
    ],
    [
        Paragraph('<font name="aa">超值产品牛步哈哈确实不错45ETTECADDD</font>',
                  styles['Normal']), '11', '12', 'A1B1104'
    ],
    [
        Paragraph('<font name="aa">超值产品牛步哈哈确实不错45ETTECADDD</font>',
                  styles['Normal']), '11', '12', 'A1B1104'
    ],
    [
        Paragraph('<font name="aa">超值产品牛步哈哈确实不错45ETTECADDD</font>',
                  styles['Normal']), '11', '12', 'A1B1104'
    ],
    ['20', '21', '22', '23'],
    ['30', '31', '32', '33'],
]
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
        ('FONTNAME', (0, 0), (-1, -1), 'aa'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
        ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
    ]))
elements.append(t)
# write the document to disk
doc.build(elements)
