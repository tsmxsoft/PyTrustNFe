# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import sys
import re
from collections import OrderedDict
from OpenSSL import crypto
import signxml
from lxml import etree
from signxml import XMLSigner
from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
from cryptography.hazmat.primitives.hashes import SHA1
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.backends import default_backend
from base64 import b64encode
from signxml.util import ensure_str
from pytrustnfe.certificado import extract_cert_and_key_from_pfx



PY2 = sys.version_info[0] == 2

class Assinatura(object):

    def __init__(self, arquivo, senha):
        self.arquivo = arquivo
        self.senha = senha

    def gerar_assinatura_rps(self, xml_send, **kwargs):
        for i, rps in enumerate(kwargs['nfse']['lista_rps']):
            chave_raw = ""
            campos = (
                #Composição: (name, max_length, rjust or ljust, padding_data)
                ('im', 8, 'rjust', '0'),                #01 - Inscrição do contribuinte
                ('serie_rps', 5, 'ljust', ' '),         #02 - Série do RPS
                ('numero_rps', 12, 'rjust', '0'),       #03 - Número do RPS
                ('dt_emissao', 8, 'ljust', ' '),        #04 - Data Emissão - yyyyMMdd
                ('trib', 1, 'ljust', ' '),              #05 - Tributação
                ('status', 1, 'rjust', '0'),            #06 - Status do RPS
                ('iss_retido', 1, 'rjust', '0'),        #07 - Tipo Recolhimento (S ou N)
                ('valor_servico', 15, 'rjust', '0'),    #08 - Valor do Serviço subtraido de deduções
                ('valor_deducoes', 15, 'rjust', '0'),   #09 - Valor da dedução
                ('cod_servico', 5, 'rjust', '0'),       #10 - Código do Serviço Prestado
                ('tomador_ind', 1, 'rjust', '0'),       #11 - Indicador de CPF/CNPJ Tomador (1 CPF 2 CNPJ 3 Não Informado)
                ('cpfcnpj_tomador', 14, 'rjust', '0'),  #12 - CPF/CNPJ do Tomador
                ('intermed_ind', 1, 'rjust', '0'),      #13 - Indicador de CPF/CNPJ Intermediário (1 CPF 2 CNPJ 3 Não Informado)
                ('cpfcnpj_intermed', 14, 'rjust', '0'), #14 - CPF/CNPJ do Intermediário
                ('iss_ret_intermed', 1, 'rjust', '0'),  #15 - ISS Retido Intermediário (S ou N)
            )

            dados = OrderedDict()
            dados['im'] = rps['prestador']['inscricao_municipal']
            dados['serie_rps'] = rps["serie"]
            dados['numero_rps'] = rps['numero']
            dados['dt_emissao'] = rps['data_emissao'].split("T")[0].replace("-","")
            dados['trib'] = rps['tipo_rps']
            dados['status'] = kwargs['nfse']['lista_rps'][i]['status']
            dados['iss_retido'] = kwargs['nfse']['lista_rps'][i]['servico']['iss_retido']
            dados['valor_servico'] = rps['servico']['valor_servico']
            dados['valor_deducoes'] = rps['servico'].get('deducoes','0.00')
            dados['cod_servico'] = rps['servico']['codigo_servico']
            if rps['tomador']['cpf_cnpj']:
                dados['tomador_ind'] = '1' if len(str(rps['tomador']['cpf_cnpj'])) == 11 else '2'
            else:
                dados['tomador_ind'] = '3'
            dados['cpfcnpj_tomador'] = rps['tomador']['cpf_cnpj']
            if rps.get('intermed',{}).get('cpf_cnpj',None):
                dados['intermed_ind'] = '1' if len(str(rps['intermed']['cpf_cnpj'])) == 11 else '2'
            else:
                dados['intermed_ind'] = '3'
            dados['cpfcnpj_intermed'] = rps.get('intermed',{}).get('cpf_cnpj','00000000000000')
            dados['iss_ret_intermed'] = rps.get('intermed',{}).get('iss_retido','N')

            #Gerar chave na ordem dos campos informada
            for campo in campos:
                chave_raw += getattr(re.sub(r'[^a-zA-Z0-9 ]', '', str(dados[campo[0]])[:campo[1]].strip()), campo[2])(campo[1],campo[3])
            
            #não é necessário informar os dados de intermediário na assinatura se não houver intermediário
            if dados['intermed_ind'] == '3':
                chave_raw = chave_raw[:-16]
            
            cert, pem = self.extract_cert_key()
            key = load_pem_private_key(pem, None, default_backend())
            signature = key.sign(chave_raw.encode('ascii'), padding=PKCS1v15(), algorithm=SHA1())
            xml_send.find('.//Assinatura[.="assinatura:%s"]' % rps['numero']).text = ensure_str(b64encode(signature))

    def extract_cert_key(self):
        pfx = crypto.load_pkcs12(self.arquivo, self.senha)
        key = crypto.dump_privatekey(crypto.FILETYPE_PEM, pfx.get_privatekey())
        cert = crypto.dump_certificate(crypto.FILETYPE_PEM, pfx.get_certificate())

        return cert, key

    def assina_xml(self, xml_element):
        cert, key = self.extract_cert_key()

        signer = XMLSigner(method=signxml.methods.enveloped, 
                           signature_algorithm="rsa-sha1",
                           digest_algorithm='sha1',
                           c14n_algorithm='http://www.w3.org/TR/2001/REC-xml-c14n-20010315')

        ns = {None: signer.namespaces['ds']}
        signer.namespaces = ns

        signed_root = signer.sign(xml_element, key=key, cert=cert)

        encoding = "utf8"        
        if sys.version_info[0] > 2:
            encoding = str
            
        xml_output = etree.tostring(signed_root, encoding=encoding)

        return xml_output

    def gerar_assinatura_cancelamento(self, xml_send, **kwargs):
        chave_raw = ""
        campos = (
            #Composição: (name, max_length, rjust or ljust, padding_data)
            ('im', 8, 'rjust', '0'),                #01 - Inscrição do contribuinte
            ('num_nfe', 12, 'rjust', '0'),          #02 - Número da NF-e
        )

        dados = OrderedDict()
        dados['im'] = kwargs['nfse']['inscricao_municipal']
        dados['num_nfe'] = kwargs['nfse']['rps']['numero']

        #Gerar chave na ordem dos campos informada
        for campo in campos:
            chave_raw += getattr(re.sub(r'[^a-zA-Z0-9 ]', '', str(dados[campo[0]])[:campo[1]].strip()), campo[2])(campo[1],campo[3])
        
        cert, pem = self.extract_cert_key()
        key = load_pem_private_key(pem, None, default_backend())
        signature = key.sign(chave_raw.encode('ascii'), padding=PKCS1v15(), algorithm=SHA1())
        xml_send.find('.//AssinaturaCancelamento').text = ensure_str(b64encode(signature))