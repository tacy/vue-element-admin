# -*- coding: utf-8 -*-

from reportlab.platypus import LongTable, TableStyle, BaseDocTemplate, Frame, PageTemplate
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors


def testPdf():
    doc = BaseDocTemplate(
        "test.pdf",
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18,
        showBoundary=True)

    elements = []
    datas = []
    for i, x in enumerate(range(1, 50)):
        datas.append([i, x])
    t = LongTable(datas)

    tableStyle = [
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
        ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
    ]
    t.setStyle(TableStyle(tableStyle))
    elements.append(t)

    frame = Frame(
        doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')
    doc.addPageTemplates([PageTemplate(id='longtable', frames=frame)])
    doc.build(elements)


if __name__ == '__main__':
    testPdf()
