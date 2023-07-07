# -*- coding: utf-8 -*-
# © 2019 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import os
from OpenSSL import crypto
from base64 import b64encode

from requests import Session
from zeep import Client
from zeep.transports import Transport
from requests.packages.urllib3 import disable_warnings

from pytrustnfe.xml import render_xml, sanitize_response
from pytrustnfe.certificado import extract_cert_and_key_from_pfx, save_cert_key
from pytrustnfe.nfe.assinatura import Assinatura
from lxml import etree
import html
import re

def _render(certificado, method, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")
    parser = etree.XMLParser(
        remove_blank_text=True, remove_comments=True, strip_cdata=False
    )
    signer = Assinatura(certificado.pfx, certificado.password)

    referencia = ""
    if method == "RecepcionarLoteRps":
        referencia = kwargs.get("nfse").get("numero_lote")

    xml_string_send = render_xml(path, "%s.xml" % "EnvelopeSoap", True, **kwargs)

    # xml object
    #xml_send = etree.fromstring(
        #xml_string_send, parser=parser)

    #for item in kwargs["nfse"]["lista_rps"]:
        #reference = "rps:{0}{1}".format(
            #item.get('numero'), item.get('serie'))

        #signer.assina_xml(xml_send, reference)

    #xml_signed_send = signer.assina_xml(
        #xml_send, "lote:{0}".format(referencia))
    
    # Soap envelope


    return xml_string_send


def _send(certificado, method, **kwargs):
    base_url = ""
    
    if kwargs["ambiente"] == "homologacao":
        base_url = "http://speedgov.com.br/wsmod/Nfes?wsdl"
    else:
        base_url = kwargs["base_url"]

    cert, key = extract_cert_and_key_from_pfx(certificado.pfx, certificado.password)
    cert, key = save_cert_key(cert, key)

    disable_warnings()
    session = Session()
    session.cert = (cert, key)
    session.verify = False
    transport = Transport(session=session)

    client = Client(wsdl=base_url, transport=transport)

    response = client.service[method](html_escape(kwargs["xml"]))
    response, obj = sanitize_response(response)
    return {"sent_xml": html_escape(kwargs["xml"]), "received_xml": response, "object": obj}

#def html_escape(xml_str):
#    params  = re.search('<parameters>(.*)<\/parameters>',xml_str,re.S)
#    replace = xml_str.replace(params.group(1),"&lt;?xml version=&quot;1.0&quot; encoding=&quot;UTF-8&quot;?&gt;" + html.escape(params.group(1)))
#    return replace.replace('&amp;','&')
def html_escape(xstr):
    return """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:nfse="http://www.abrasf.org.br/ABRASF/arquivos/nfse.xsd">
   <soapenv:Header/>
   <soapenv:Body>
      <nfse:RecepcionarLoteRps>
         <!--Optional:-->
         <header>&lt;?xml version=&quot;1.0&quot; encoding=&quot;UTF-8&quot;?&gt;&lt;p:cabecalho versao=&quot;1&quot; xmlns:ds=&quot;http://www.w3.org/2000/09/xmldsig#&quot; xmlns:p=&quot;http://ws.speedgov.com.br/cabecalho_v1.xsd&quot; xmlns:p1=&quot;http://ws.speedgov.com.br/tipos_v1.xsd&quot; xmlns:xsi=&quot;http://www.w3.org/2001/XMLSchema-instance&quot; xsi:schemaLocation=&quot;http://ws.speedgov.com.br/cabecalho_v1.xsd cabecalho_v1.xsd &quot;&gt;&lt;versaoDados&gt;1&lt;/versaoDados&gt;&lt;/p:cabecalho&gt;</header>
         <!--Optional:-->
         <parameters>&lt;?xml version=&quot;1.0&quot; encoding=&quot;UTF-8&quot;?&gt;
&lt;p:EnviarLoteRpsEnvio xmlns:ds=&quot;http://www.w3.org/2000/09/xmldsig#&quot; xmlns:p=&quot;http://ws.speedgov.com.br/enviar_lote_rps_envio_v1.xsd&quot; xmlns:p1=&quot;http://ws.speedgov.com.br/tipos_v1.xsd&quot; xmlns:xsi=&quot;http://www.w3.org/2001/XMLSchema-instance&quot; xsi:schemaLocation=&quot;http://ws.speedgov.com.br/enviar_lote_rps_envio_v1.xsd enviar_lote_rps_envio_v1.xsd &quot;&gt;
  &lt;p:LoteRps Id=&quot;&quot;&gt;
    &lt;p1:NumeroLote&gt;2&lt;/p1:NumeroLote&gt;
    &lt;p1:Cnpj&gt;57255426000103&lt;/p1:Cnpj&gt;
    &lt;p1:InscricaoMunicipal&gt;1&lt;/p1:InscricaoMunicipal&gt;
    &lt;p1:QuantidadeRps&gt;1&lt;/p1:QuantidadeRps&gt;
    &lt;p1:ListaRps&gt;
      &lt;p1:Rps&gt;
        &lt;p1:InfRps Id=&quot;&quot;&gt;
          &lt;p1:IdentificacaoRps&gt;
            &lt;p1:Numero&gt;1&lt;/p1:Numero&gt;
            &lt;p1:Serie&gt;00000&lt;/p1:Serie&gt;
            &lt;p1:Tipo&gt;1&lt;/p1:Tipo&gt;
          &lt;/p1:IdentificacaoRps&gt;
          &lt;p1:DataEmissao&gt;2013-10-01T08:10:00&lt;/p1:DataEmissao&gt;
          &lt;p1:NaturezaOperacao&gt;1&lt;/p1:NaturezaOperacao&gt;
          &lt;p1:OptanteSimplesNacional&gt;2&lt;/p1:OptanteSimplesNacional&gt;
          &lt;p1:IncentivadorCultural&gt;2&lt;/p1:IncentivadorCultural&gt;
          &lt;p1:Status&gt;1&lt;/p1:Status&gt;
          &lt;p1:Servico&gt;
            &lt;p1:Valores&gt;
              &lt;p1:ValorServicos&gt;500.0&lt;/p1:ValorServicos&gt;
              &lt;p1:ValorDeducoes&gt;0.0&lt;/p1:ValorDeducoes&gt;
              &lt;p1:ValorPis&gt;0.0&lt;/p1:ValorPis&gt;
              &lt;p1:ValorCofins&gt;0.0&lt;/p1:ValorCofins&gt;
              &lt;p1:ValorInss&gt;0.0&lt;/p1:ValorInss&gt;
              &lt;p1:ValorIr&gt;0.0&lt;/p1:ValorIr&gt;
              &lt;p1:ValorCsll&gt;0.0&lt;/p1:ValorCsll&gt;
              &lt;p1:IssRetido&gt;2&lt;/p1:IssRetido&gt;              
              &lt;p1:ValorIss&gt;10.0&lt;/p1:ValorIss&gt;
              &lt;p1:ValorIssRetido&gt;0.0&lt;/p1:ValorIssRetido&gt;
              &lt;p1:OutrasRetencoes&gt;0.0&lt;/p1:OutrasRetencoes&gt;
              &lt;p1:BaseCalculo&gt;500.0&lt;/p1:BaseCalculo&gt;
              &lt;p1:Aliquota&gt;2.0&lt;/p1:Aliquota&gt;
              &lt;p1:ValorLiquidoNfse&gt;490.0&lt;/p1:ValorLiquidoNfse&gt;
              &lt;p1:DescontoCondicionado&gt;0.0&lt;/p1:DescontoCondicionado&gt;
              &lt;p1:DescontoIncondicionado&gt;0.0&lt;/p1:DescontoIncondicionado&gt;
            &lt;/p1:Valores&gt;
            &lt;p1:ItemListaServico&gt;101&lt;/p1:ItemListaServico&gt;
            &lt;p1:CodigoCnae&gt;6201500&lt;/p1:CodigoCnae&gt;
            &lt;p1:CodigoTributacaoMunicipio&gt;620150000&lt;/p1:CodigoTributacaoMunicipio&gt;
            &lt;p1:Discriminacao&gt;SERVICO TESTE&lt;/p1:Discriminacao&gt;
            &lt;p1:CodigoMunicipio&gt;9999999&lt;/p1:CodigoMunicipio&gt;
          &lt;/p1:Servico&gt;
          &lt;p1:Prestador&gt;
            &lt;p1:Cnpj&gt;57255426000103&lt;/p1:Cnpj&gt;
            &lt;p1:InscricaoMunicipal&gt;1&lt;/p1:InscricaoMunicipal&gt;
          &lt;/p1:Prestador&gt;
          &lt;p1:Tomador&gt;
            &lt;p1:IdentificacaoTomador&gt;
              &lt;p1:CpfCnpj&gt;
                &lt;p1:Cnpj&gt;12477945000188&lt;/p1:Cnpj&gt;
              &lt;/p1:CpfCnpj&gt;
            &lt;/p1:IdentificacaoTomador&gt;
            &lt;p1:RazaoSocial&gt;TESTE EUGENIO SALVIANO&lt;/p1:RazaoSocial&gt;            
            &lt;p1:Endereco&gt;
              &lt;p1:Endereco&gt;RUA VICENTE F. GOES&lt;/p1:Endereco&gt;
              &lt;p1:Numero&gt;182&lt;/p1:Numero&gt;
              &lt;p1:Complemento&gt;A&lt;/p1:Complemento&gt;
              &lt;p1:Bairro&gt;ALTO DA MANGUEIRA&lt;/p1:Bairro&gt;
              &lt;p1:CodigoMunicipio&gt;9999999&lt;/p1:CodigoMunicipio&gt;
              &lt;p1:Uf&gt;CE&lt;/p1:Uf&gt;
              &lt;p1:Cep&gt;61900000&lt;/p1:Cep&gt;
            &lt;/p1:Endereco&gt;
            &lt;p1:Contato&gt;
              &lt;p1:Telefone&gt;8512341234&lt;/p1:Telefone&gt;
              &lt;p1:Email&gt;teste@fes.com.br&lt;/p1:Email&gt;
            &lt;/p1:Contato&gt;
          &lt;/p1:Tomador&gt;
          &lt;p1:IntermediarioServico&gt;
            &lt;p1:RazaoSocial&gt;Intersol Servicos Ltda&lt;/p1:RazaoSocial&gt;
            &lt;p1:CpfCnpj&gt;
              &lt;p1:Cpf&gt;89746104349&lt;/p1:Cpf&gt;
            &lt;/p1:CpfCnpj&gt;
            &lt;p1:InscricaoMunicipal&gt;1234567&lt;/p1:InscricaoMunicipal&gt;
          &lt;/p1:IntermediarioServico&gt;
        &lt;/p1:InfRps&gt;
      &lt;/p1:Rps&gt;
    &lt;/p1:ListaRps&gt;
  &lt;/p:LoteRps&gt;
&lt;/p:EnviarLoteRpsEnvio&gt;
</parameters>
      </nfse:RecepcionarLoteRps>
   </soapenv:Body>
</soapenv:Envelope>""".replace('\n','')

def xml_recepcionar_lote_rps(certificado, **kwargs):
    return _render(certificado, "RecepcionarLoteRps", **kwargs)

def recepcionar_lote_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_recepcionar_lote_rps(certificado, **kwargs)
    return _send(certificado, "RecepcionarLoteRps", **kwargs)

def xml_consultar_lote_rps(certificado, **kwargs):
    return _render(certificado, "ConsultarLoteRps", **kwargs)

def consultar_lote_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_consultar_lote_rps(certificado, **kwargs)
    return _send(certificado, "ConsultarLoteRps", **kwargs)

def xml_cancelar_nfse(certificado, **kwargs):
    return _render(certificado, "cancelarNfse", **kwargs)

def cancelar_nfse(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_cancelar_nfse(certificado, **kwargs)
    return _send(certificado, "cancelarNfse", **kwargs)
