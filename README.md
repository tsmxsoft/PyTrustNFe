# PyTrustNFe
Biblioteca Python que tem por objetivo enviar NFe, NFCe e NFSe no Brasil

[![Coverage Status](https://coveralls.io/repos/thiagosm/PyTrustNFe/badge.svg?branch=master3)](https://coveralls.io/r/thiagosm/PyTrustNFe?branch=master3)
[![Code Health](https://landscape.io/github/thiagosm/PyTrustNFe/master3/landscape.svg?style=flat)](https://landscape.io/github/thiagosm/PyTrustNFe/master3)
[![Build Status](https://travis-ci.org/thiagosm/PyTrustNFe.svg?branch=master3)](https://travis-ci.org/thiagosm/PyTrustNFe)
[![PyPI version](https://badge.fury.io/py/PyTrustNFe3.svg)](https://badge.fury.io/py/PyTrustNFe3)

Dependências:
* PyXmlSec
* lxml
* signxml
* suds-jurko
* suds-jurko-requests
* reportlab
* Jinja2
* requests
* zeep


NFSe - Empresas Atendidas
-----------------------------
* **Agiliblue**
* **Betha**
* **Cariacica** - Cariacica/ES
* **Directa** - Natal/RN
* **DSF**
* **GINFES**
* **Imperial** - Petrópolis/RH
* **ISSNET**
* **ISSWEB**
* **Memory (NFSe Brasil)**
* **Nota Carioca** - Rio de Janeiro/RJ
* **Paulistana** - São Paulo/SP
* **Recife** - Recife/PE
* **SIASP (Publica)**
* **Speedgov**
* **Susesu**
* **Simpliss**
* **Tinus Informatica**
* **Tecnos**
* **WebISS**

Roadmap
--------------
* Teste unitários
* Objeto padronizado de retorno (Padronização e implementação)
* NFCom (NF Modelo 62)
* NFSe Tributus
* NFSe GSN - Salvador

Padronizações
--------------
* As integrações contém URL direta para ambiente de homologação, porém para ambiente de produção, é necessário passar o parâmetro **kwargs["base_url"]**, pois alguns sistemas tem URL única em produção, outros possuem uma URL para cada cidade atendida, para abranger todos os casos, esse parâmetro foi implementado.

Exemplos de uso da NFe
-----------------------------

Consulta Cadastro por CNPJ:

```python
from pytrustnfe.nfe import consulta_cadastro
from pytrustnfe.certificado import Certificado

certificado = open("/path/certificado.pfx", "r").read()
certificado = Certificado(certificado, 'senha_pfx')
obj = {'cnpj': '12345678901234', 'estado': '42'}
resposta = consulta_cadastro(certificado, obj=obj, ambiente=1, estado='42')
```
Consulta Distribuição NF-e sem Validação de Esquema:
```python
from pytrustnfe.certificado import Certificado
from pytrustnfe.nfe import consulta_distribuicao_nfe, xml_consulta_distribuicao_nfe

certificado = open("/path/certificado.pfx", "r").read()
certificado = Certificado(certificado, 'senha_pfx')

# Gerando xml e enviado consulta por Ultimo NSU
response1 = consulta_distribuicao_nfe(
    certificado,
    ambiente=1,
    estado='42',
    modelo='55',
    cnpj_cpf='12345678901234',
    ultimo_nsu='123456789101213'
)

# Gerando xml e enviado consulta por Chave
response2 = consulta_distribuicao_nfe(
    certificado,
    ambiente=1,
    estado='42',
    modelo='55',
    cnpj_cpf='12345678901234',
    chave_nfe='012345678901234567890123456789012345678912'
)

# Gerando xml e enviado consulta por NSU
response3 = consulta_distribuicao_nfe(
    certificado,
    ambiente=1,
    estado='42',
    modelo='55',
    cnpj_cpf='12345678901234',
    nsu='123456789101213'
)
```

Consulta Distribuição NF-e com Validação de Esquema:
```python
from pytrustnfe.certificado import Certificado
from pytrustnfe.nfe import consulta_distribuicao_nfe, xml_consulta_distribuicao_nfe
from pytrustnfe.xml.validate import valida_nfe, SCHEMA_DFE

certificado = open("/path/certificado.pfx", "r").read()
certificado = Certificado(certificado, 'senha_pfx')

# Gerando XML para Consulta por Ultimo NSU
xml1 = xml_consulta_distribuicao_nfe(
    certificado,
    ambiente=1,
    estado='42',
    cnpj_cpf='12345678901234',
    ultimo_nsu='123456789101213'
)

# Validando o XML com Esquema
if valida_nfe(xml1, SCHEMA_DFE):
    Warning("Erro na validação do esquema")
    
# Gerando XML para Consulta por Chave
xml2 = xml_consulta_distribuicao_nfe(
    certificado,
    ambiente=1,
    estado='42',
    cnpj_cpf='12345678901234',
    chave_nfe='012345678901234567890123456789012345678912'
)

# Validando o XML com Esquema
if valida_nfe(xml2, SCHEMA_DFE):
    Warning("Erro na validação do esquema")
    
# Gerando XML para Consulta por NSU
xml3 = xml_consulta_distribuicao_nfe(
    certificado,
    ambiente=1,
    estado='42',
    cnpj_cpf='12345678901234',
    nsu='123456789101213'
)

# Validando o XML com Esquema
if valida_nfe(xml3, SCHEMA_DFE):
    Warning("Erro na validação do esquema")

# Enviando xml de consulta para sefaz
response = consulta_distribuicao_nfe(
    certificado,
    ambiente=1,
    estado='42',
    modelo='55',
    xml=xml1
)
```

Exemplo de uso da NFSe Paulistana
---------------------------------

Envio de RPS por lote

```python
certificado = open('/path/certificado.pfx', 'r').read()
certificado = Certificado(certificado, '123456')
# Necessário criar um dicionário com os dados, validação dos dados deve
# ser feita pela aplicação que está utilizando a lib
rps = [
    {
        'assinatura': '123',
        'serie': '1',
        'numero': '1',
        'data_emissao': '2016-08-29',
        'codigo_atividade': '07498',
        'valor_servico': '2.00',
        'valor_deducao': '3.00',
        'prestador': {
            'inscricao_municipal': '123456'
        },
        'tomador': {
            'tipo_cpfcnpj': '1',
            'cpf_cnpj': '12345678923256',
            'inscricao_municipal': '123456',
            'razao_social': 'Trustcode',
            'tipo_logradouro': '1',
            'logradouro': 'Vinicius de Moraes, 42',
            'numero': '42',
            'bairro': 'Corrego',
            'cidade': '4205407',  # Código da cidade, de acordo com o IBGE
            'uf': 'SC',
            'cep': '88037240',
        },
        'codigo_atividade': '07498',
        'aliquota_atividade': '5.00',
        'descricao': 'Venda de servico'
    }
]
nfse = {
    'cpf_cnpj': '12345678901234',
    'data_inicio': '2016-08-29',
    'data_fim': '2016-08-29',
    'total_servicos': '2.00',
    'total_deducoes': '3.00',
    'lista_rps': rps
}

retorno = envio_lote_rps(certificado, nfse=nfse)
# retorno é um dicionário { 'received_xml':'', 'sent_xml':'', 'object': object() }
print retorno['received_xml']
print retorno['sent_xml']

# retorno['object'] é um objeto python criado apartir do xml de resposta
print retorno['object'].Cabecalho.Sucesso
print retorno['object'].ChaveNFeRPS.ChaveNFe.NumeroNFe
print retorno['object'].ChaveNFeRPS.ChaveRPS.NumeroRPS
```


Cancelamento de NFSe:

```python
from pytrustnfe.certificado import Certificado
from pytrustnfe.nfse.paulistana import cancelamento_nfe

certificado = open('/path/certificado.pfx', 'r').read()
certificado = Certificado(certificado, '123456')
cancelamento = {
    'cnpj_remetente': '123',
    'assinatura': 'assinatura',
    'numero_nfse': '456',
    'inscricao_municipal': '654',
    'codigo_verificacao': '789',
}

retorno = cancelamento_nfe(certificado, cancelamento=cancelamento)

# retorno é um dicionário { 'received_xml':'', 'sent_xml':'', 'object': object() }
print retorno['received_xml']
print retorno['sent_xml']

# retorno['object'] é um objeto python criado apartir do xml de resposta
print retorno['object'].Cabecalho.Sucesso

if not retorno['object'].Cabecalho.Sucesso: # Cancelamento com erro
    print retorno['object'].Erro.Codigo
    print retorno['object'].Erro.Descricao
```
