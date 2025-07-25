# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import os
from pytrustnfe.xml import render_xml, sanitize_response
from pytrustnfe.certificado import extract_cert_and_key_from_pfx, save_cert_key
from pytrustnfe.nfse.novaIguacu.assinatura import Assinatura
from lxml import etree
from requests import Session
import requests
import hashlib
from pytrustnfe.utils import ibge2siafi
from decimal import Decimal


def clean_x509(xml_string):
    parser = etree.XMLParser(remove_blank_text=True, remove_comments=True, strip_cdata=False)
    root = etree.fromstring(xml_string, parser=parser)


    for elem in root.iter():
        if elem.tag.endswith('X509Certificate'):
            if '\n' in elem.text:
                elem.text = elem.text.replace('\n', '')
    return etree.tostring(root, encoding='unicode')



def _render(certificado, method, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")
    parser = etree.XMLParser(
        remove_blank_text=True, remove_comments=True, strip_cdata=False
    )
    signer = Assinatura(certificado.pfx, certificado.password)

    referencia = ""
    if method == "RecepcionarLoteRpsSincrono" or method == "enviar":
        cnpj_pref = kwargs["nfse"].get("cnpj_prefeitura", None)
        ibge_cid_tomador = kwargs.get("nfse", {}).get("lista_rps", [{}])[0].get("tomador", {}).get("codigo_municipio", None)
        ibge_cid_servico = kwargs.get("nfse", {}).get("lista_rps", [{}])[0].get("servico", {}).get("codigo_municipio", None)

        for rps in kwargs["nfse"]["lista_rps"]:
            rps["servico"]["codigo_municipio"] = ibge2siafi(ibge_cid_servico) \
                if ibge_cid_servico else cnpj_pref
            rps["tomador"]["codigo_municipio"] = ibge2siafi(ibge_cid_tomador) \
                if ibge_cid_tomador else cnpj_pref
        
        referencia = kwargs.get('nfse').get('numero_lote')
        
    xml_string_send = render_xml(path, "%s.xml" % method, True, False, **kwargs)

    # xml object
    xml_send = etree.fromstring(
        xml_string_send, parser=parser)


    if method in ["enviar",
                "RecepcionarLoteRpsSincrono"]:
                
        for item in kwargs["nfse"]["lista_rps"]:
            reference = "rps:{0}{1}".format(
                item.get('numero'), item.get('serie'))

            # signer.assina_xml(xml_send, reference)
            # signer.gerar_assinatura_rps(**kwargs)

        xml_signed_send = signer.assina_xml(
            xml_send, "lote:{0}".format(referencia))
        
        
    # # Assinar o XML para cancelamento 
    # elif method == "cancelar":
    #     referencia = kwargs.get('nfse').get('numero')
    #     xml_signed_send = signer.assina_xml(xml_send, 'nota:{0}'.format(kwargs.get('nfse').get('numero')))


    else:
        print('--- xml ---')
        print(xml_string_send)
        return xml_string_send

    print('--- xml ---')
    print(xml_signed_send)
    return xml_signed_send


def _send(certificado, method, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")

    base_url = None
    try:
        base_url = kwargs.get('base_url')
    except:
        raise Exception("É obrigatório informar a url")

    xml_send = kwargs["xml"]
    path = os.path.join(os.path.dirname(__file__), "templates")
    soap = render_xml(path, "SoapRequest.xml", False, False, **{"soap_body":xml_send, "method": method })

    cert, key = extract_cert_and_key_from_pfx(certificado.pfx, certificado.password)
    cert, key = save_cert_key(cert, key)
    session = Session()
    session.cert = (cert, key)
    session.verify = False
    action = "http://nfse.abrasf.org.br/%s" %(method)
    headers = {
        "Content-Type": "text/xml;charset=UTF-8",
        "SOAPAction": action,
        "Operation": method,
        "Content-length": str(len(soap))
    }

    request = requests.post(base_url, data=soap, headers=headers)
    response, obj = sanitize_response(request.content.decode('utf8', 'ignore'))
    return {"sent_xml": str(soap), "received_xml": str(response), "object": obj.Body }


####### RECEPCIONAR LOTE RPS #######

def recepcionar_lote_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_recepcionar_lote_rps(certificado, **kwargs)
    return _send(certificado, "enviar", **kwargs)

def xml_recepcionar_lote_rps(certificado, **kwargs):
    for i, rps in enumerate(kwargs['nfse']['lista_rps']):
        assinatura = ''

        inscricao_municipal = kwargs.get('nfse').get('inscricao_municipal')
        assinatura += inscricao_municipal.zfill(11)
        assinatura += 'NF'
        assinatura += '   '
        assinatura += rps['numero'].zfill(12)
        assinatura += rps['data_emissao'][:10].replace('-', '')
        assinatura += 'H'
        assinatura += ' '
        assinatura += 'N' if rps['status'] == '1' else 'C'
        recolhimento = rps['servico']['iss_retido'] = 'N' if rps['servico']['iss_retido'] == '2' else 'S'
        assinatura += recolhimento
        servico_deducao = float(rps['servico']['valor_servico']) - float(rps['servico'].get('deducoes', 0.00))
        servico_deducao = str(servico_deducao).replace('.', '').replace(',', '').zfill(15) 
        assinatura += servico_deducao
        assinatura += str(rps['servico'].get('deducoes', 0.00)).replace('.', '').replace(',', '.').zfill(15)    
        assinatura += rps['servico']['cnae_servico'].replace('.', '').replace('-', '').zfill(10)
        assinatura += rps['tomador']['cpf_cnpj'].replace('.', '').replace('-', '').zfill(14)

        assinatura_slice = [assinatura[i:i+94] for i in range(0, len(assinatura), 94)]
        hash_assinatura = []
        for slice in assinatura_slice:
            hash_assinatura.append(hashlib.sha1(slice.encode('utf-8')).hexdigest())

        for assinatura in hash_assinatura:
            rps['assinatura'] = assinatura

    kwargs['nfse']['total_servicos'] = '{0:.2f}'.format(sum(Decimal(rps['servico']['valor_servico']) \
                            for rps in kwargs['nfse']['lista_rps']))
    
    kwargs['nfse']['total_deducoes'] = '{0:.2f}'.format(sum(Decimal(rps['servico']['deducoes']) \
                            for rps in kwargs['nfse']['lista_rps'] if 'deducoes' in rps['servico']))
    
    for i, rps in enumerate(kwargs['nfse']['lista_rps']):
        # Operação
        operacao = None
        # C - Imune/Isenta de ISS
        if str(rps['eligibilidade_iss']) in ['3', '5']:
            operacao = 'C'

        # B - Com Dedução/Materiais
        elif 'deducoes' in rps['servico'] and not rps['servico']['deducoes'] == '0.00':
            operacao = 'B'
        # J - Intermediário
        elif 'intermediario' in rps:
            operacao = 'J'
        # A - Sem dedução
        else:
            operacao = 'A'
        kwargs['nfse']['lista_rps'][i]['operacao'] = operacao
        
        # Tributação
        tributacao = None
        #M – Micro Empreendedor Individual (MEI)
        if str(rps['regime_tributacao']) == '5':
            tributacao = 'M'
        #C - Isenta de ISS
        elif str(rps['natureza_operacao']) == '3':
            tributacao = 'C'
        #F - Imune
        elif str(rps['natureza_operacao']) == '4':
            tributacao = 'F'
        #K – Exigibilidade Sus.Dec. J/Proc.A
        elif str(rps['natureza_operacao']) in ['5','6']:
            tributacao = 'K'
        #H - Tributável - Simples Nacional
        elif str(rps['optante_simples']) == '1':
            tributacao = 'H'
        #E - Não Incidência no Município
        elif str(rps['natureza_operacao']) in ['1','2'] and str(rps['servico']['codigo_municipio']) != str(rps['tomador']['codigo_municipio']):
            tributacao = 'E'
        #N - Não tributável
        elif str(rps['natureza_operacao']) in ['1','2'] and str(rps['servico']['iss']) == '0.00':
            tributacao = 'N'
        #T - Tributável
        elif str(rps['natureza_operacao']) in ['1','2'] and Decimal(rps['servico']['iss']) > Decimal('0.00'):
            tributacao = 'T'
        else:
            #G - Tributável Fixo
            tributacao = 'G'
        
        kwargs['nfse']['lista_rps'][i]['tributacao'] = tributacao

    return clean_x509(_render(certificado, "enviar", **kwargs))

#######################################



####### CONSULTAR LOTE RPS #######

def xml_consultar_lote_rps(certificado, **kwargs):
    return _render(certificado, "consultarLote", **kwargs)


def consultar_lote_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_consultar_lote_rps(certificado, **kwargs)
    return _send(certificado, "consultarLote", **kwargs)

#######################################


####### CONSULTAR NFSe POR RPS #######

def xml_consultar_nfse_por_rps(certificado, **kwargs):    
    return _render(certificado, "consultarNFSeRps", **kwargs)

def consultar_nfse_por_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_consultar_nfse_por_rps(certificado, **kwargs)
    response = _send(certificado, "consultarNFSeRps", **kwargs)
    xml = None

#######################################



####### CONSULTAR NOTA #######

def xml_consultar_nota(certificado, **kwargs):
    return _render(certificado, "consultarNota", **kwargs)


def consultar_nota(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_consultar_nota(certificado, **kwargs)
    return _send(certificado, "consultarNota", **kwargs)

#######################################



####### CANCELAR NOTA #######

def xml_cancelar_nfse(certificado, **kwargs):
    return _render(certificado, "cancelar", **kwargs)


def cancelar_nfse(certificado, **kwargs):
    if 'xml' not in kwargs:
        kwargs['xml'] = xml_cancelar_nfse(certificado, **kwargs)
    return _send(certificado, "cancelar", **kwargs)

#######################################