# -*- coding: utf-8 -*-
import os
import json
import logging
import eventlet
import gspread
from oauth2client.client import SignedJwtAssertionCredentials

log = logging.getLogger(__name__)


def open_google_doc(doc_name):
    cdir = os.path.dirname(os.path.abspath(__file__))
    json_key = json.load(
        open(os.path.join(cdir, 'tacy-speedsheet-d32988f60e38.json')))
    scope = ['https://spreadsheets.google.com/feeds']

    credentials = SignedJwtAssertionCredentials(json_key['client_email'],
                                                json_key['private_key'], scope)
    sp = None
    try:
        with eventlet.Timeout(120):
            gc = gspread.authorize(credentials)
            sp = gc.open(doc_name)
    except (Exception, eventlet.Timeout):
        log.exception('Open google doc failed')
        raise
    return sp


def read_google_doc_by_col(doc, wks_name, col):
    wks = doc.worksheet(wks_name)
    return wks.col_values(col)


def read_google_doc_by_range(doc, wks_name, rangestr, all_rows=False):
    wks = doc.worksheet(wks_name)
    if all_rows:
        count = wks.row_count
        rangestr = rangestr + str(count)
    r = wks.range(rangestr)
    return [i.value for i in r]


def write_google_doc(doc, wks_name, data, size, mode, left, right):
    c_range = None
    wks = doc.worksheet(wks_name)
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
