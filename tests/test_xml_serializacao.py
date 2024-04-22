# coding=utf-8

import os.path
import sys
import unittest
from lxml import etree
from pytrustnfe.xml import render_xml
from pytrustnfe.xml import sanitize_response

if sys.version_info >= (3, 0):
    unicode = str

class test_xml_serializacao(unittest.TestCase):
    def test_serializacao_default(self):
        path = os.path.join(os.path.dirname(__file__), "XMLs")
        xml = render_xml(
            path, "jinja_template.xml", False, tag1="oi", tag2="ola", tag3="comovai"
        )

        file = open(os.path.join(path, "jinja_result.xml"), "r")
        result = file.read()
        self.assertEqual(xml + "\n", result)
        file.close()

    def test_serializacao_remove_empty(self):
        path = os.path.join(os.path.dirname(__file__), "XMLs")
        xmlElem = render_xml(
            path, "jinja_template.xml", True, tag1="oi", tag2="ola", tag3="comovai"
        )
        file = open(os.path.join(path, "jinja_remove_empty.xml"), "r")
        result = file.read()
        self.assertEqual(xmlElem + "\n", result)
        file.close()

    def test_sanitize_response(self):
        path = os.path.join(os.path.dirname(__file__), "XMLs")
        file = open(os.path.join(path, "jinja_result.xml"), "r")
        xml_to_clear = file.read()
        xml, obj = sanitize_response(xml_to_clear)
        self.assertEqual(xml, xml_to_clear)
        self.assertEqual(obj.tpAmb, "oi")
        self.assertEqual(obj.CNPJ, "ola")
        self.assertEqual(obj.indNFe, "")
        self.assertEqual(obj.indEmi, "comovai")
        file.close()
