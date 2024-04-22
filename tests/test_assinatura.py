# coding=utf-8
"""
Created on Jun 14, 2015

@author: danimar
"""
import os
import sys
import os.path
import unittest
from lxml import etree
from pytrustnfe.nfe.assinatura import Assinatura

if sys.version_info[0] < 3:
    str = unicode

XML_ASSINAR = str(
    '<Envelope xmlns="urn:envelope">'
    '   <Data Id="NFe43150602261542000143550010000000761792265342">'
    "     Hello, World!"
    "   </Data>"
    "</Envelope>"
)


XML_ERRADO = str(
    '<Envelope xmlns="urn:envelope">'
    ' <Data Id="NFe">'
    "     Hello, World!"
    "   </Data>"
    "</Envelope>"
)


class test_assinatura(unittest.TestCase):

    __name__ = 'assinatura'
    caminho = os.path.dirname(__file__)

    def test_assinar_xml_senha_invalida(self):
        file = open(os.path.join(self.caminho, "teste.pfx"), "rb")
        pfx = file.read()
        signer = Assinatura(pfx, "123")
        self.assertRaises(
            Exception,
            signer.assina_xml,
            signer,
            etree.fromstring(XML_ASSINAR),
            "NFe43150602261542000143550010000000761792265342",
        )
        file.close()

    def test_assinar_xml_invalido(self):
        file = open(os.path.join(self.caminho, "teste.pfx"), "rb")
        pfx = file.read()
        signer = Assinatura(pfx, "123456")
        self.assertRaises(
            Exception,
            signer.assina_xml,
            signer,
            etree.fromstring(XML_ERRADO),
            "NFe43150602261542000143550010000000761792265342",
        )
        file.close()

    def test_assinar_xml_valido(self):
        file = open(os.path.join(self.caminho, "teste.pfx"), "rb")
        pfx = file.read()
        signer = Assinatura(pfx, "123456")
        xml = signer.assina_xml(
            etree.fromstring(XML_ASSINAR),
            "NFe43150602261542000143550010000000761792265342",
        )
        file_assinado = open(
            os.path.join(self.caminho, "xml_valido_assinado.xml"), "r"
        )
        xml_assinado = file_assinado.read()
        file.close()
        file_assinado.close()
        self.assertEqual(xml_assinado, xml, "Xml assinado é inválido")