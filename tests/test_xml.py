# coding=utf-8
"""
Created on Jun 14, 2015

@author: danimar
"""
import sys
import unittest
from datetime import datetime
from decimal import Decimal
from pytrustnfe.xml.filters import normalize_str
from pytrustnfe.xml.filters import strip_line_feed
from pytrustnfe.xml.filters import format_percent
from pytrustnfe.xml.filters import format_datetime
from pytrustnfe.xml.filters import format_datetime_dmy
from pytrustnfe.xml.filters import format_datetime_ymd
from pytrustnfe.xml.filters import format_datetime_wslashes_ymd
from pytrustnfe.xml.filters import format_numeric
from pytrustnfe.xml.filters import format_datetime_hms
from pytrustnfe.xml.filters import format_cep
from pytrustnfe.xml.filters import format_date
from pytrustnfe.xml.filters import format_with_comma

if sys.version_info >= (3, 0):
    unicode = str

class test_xmlfilters(unittest.TestCase):
    def test_xmlfilters(self):
        word = normalize_str("ação café pó pá veêm")
        self.assertEqual(word, "acao cafe po pa veem")
        self.assertEqual(1.5, format_percent(150))
        self.assertEqual("aa", format_date("aa"))
        self.assertEqual("aa", format_datetime("aa"))

        dt = datetime(2016, 9, 17, 12, 12, 12)
        self.assertEqual("2016-09-17", format_date(dt.date()))
        self.assertEqual("2016-09-17T12:12:12", format_datetime(dt))
        self.assertEqual("17/09/2016",format_datetime_dmy("2016-09-17T12:12:12"))
        self.assertEqual("2016-09-17",format_datetime_ymd("2016-09-17T12:12:12"))
        self.assertEqual("12:12:12",format_datetime_hms("2016-09-17T12:12:12"))
        self.assertEqual("2016-09-17",format_datetime_wslashes_ymd("20160917T121212"))
        self.assertEqual("0013,0000",format_numeric("13",9,4,True,True))
        self.assertEqual("55111-999", format_cep("55111999"))
        self.assertEqual("55111-999", format_cep("55111-999"))
        self.assertEqual("5,50", format_with_comma(5.50))
        self.assertEqual("5,50", format_with_comma(Decimal("5.50")))
        self.assertEqual("5,00", format_with_comma(5))
        self.assertEqual("5,00", format_with_comma("5"))

        word = strip_line_feed("olá\ncomo vai\r senhor ")
        self.assertEqual(word, u"olá como vai senhor")
