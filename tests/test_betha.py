# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import os.path
import unittest
from pytrustnfe.certificado import Certificado


class test_nfse_betha(unittest.TestCase):

    __name__ = "nfse_betha"
    caminho = os.path.dirname(__file__)

    @unittest.skip
    def test_consulta_situacao_lote(self):
        pfx_source = open("teste.pfx", "rb").read()
        pfx = Certificado(pfx_source, "123")

        dados = {"ambiente": "homologacao"}

        self.assertNotEqual(retorno["received_xml"], "")
        self.assertEqual(retorno["object"].Cabecalho.Sucesso, True)
