# Variáveis novas a serem adequadas no SGP

Seguem abaixo as variáveis criadas para adaptação no SGP, após resolvidas favor remover esse markdown

## CancelarNFSe
- {{ cancelamento.cnpj_prefeitura }} (CNPJ da prefeitura, apenas números)

## ConsultarLoteRps
- {{ consulta.cnpj_prefeitura }} (CNPJ da prefeitura, apenas números)

## ConsultarNfseFaixa
- {{ consulta.cnpj_prefeitura }} (CNPJ da prefeitura, apenas números)
- {{ consulta.nfse_faixa_inicio }} Inicio da faixa de numeração da NFS-e
- {{ consulta.nfse_faixa_fim }} Fim da faixa de numeração da NFS-e

## ConsultarNfseRps
- {{ consulta.cnpj_prefeitura }} (CNPJ da prefeitura, apenas números)
- {{ consulta.nfse_rps_numero }} (inteiro, não-negativo)
- {{ consulta.nfse_rps_serie }} (string, length 5)
- {{ consulta.nfse_rps_tipo }} (inteiro, negativo, [-2] = RPS; [-4] = Nota fiscal conjugada (mista); [-5] Cupom.)

## ConsultarRequerimentoCancelamento
- {{ consulta.cnpj_prefeitura }} (CNPJ da prefeitura, apenas números)

