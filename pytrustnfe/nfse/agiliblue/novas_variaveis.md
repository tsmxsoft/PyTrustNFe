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

## RecepcionarLoteRps
- {{ nfse.cnpj_prefeitura }} (CNPJ da prefeitura, apenas números)
- {{ nfse.assinatura }} (Chave Digital)

## Rps
- {{ rps.assinatura }} (Chave Digital)
- {{ rps.tomador.complemento }} (Complemento do endereço do tomador)
- {{ rps.tomador.cidade }} (Nome da cidade)
- {{ rps.servico.valor_descontos }} (Valor do somatório dos descontos de todos os serviços)
- {{ rps.tomador.inscricao_estadual }} (Inscrição estadual, string, length 20)
- {{ rps.optante_mei_simei }} (Se o prestador do serviço MEI (microempreendedor individual) é optante do SIMEI. [1] – Sim [0] – Não)
- {{ rps.iss_cod_responsavel }} (Código do responsável pelo ISS junto à administração pública municipal)
- {{ rps.itemlei116_atividade_economica }} (Código do item de serviço conforme a Lei 116 de 2003, string, length 140)
- {{ rps.iss_exigibilidade_cod }} (Código de exigibilidade da ISS; [-1] Exigível. [-2] Não incidência. [-3] Isento. [-4] Exportação. [-5] Imune. [-6] Exigibilidade suspensa por decisão judicial. [-7] Exigibilidade suspensa por processo administrativo. [-8] Fixo. [-9] Isento por lei específica )
- {{ rps.beneficio_processo }} (Número do processo judicial ou administrativo de suspensão de exigibilidade ou número do processo de isenção de ISSQN da atividade econômica.)
- {{ rps.servico.observacao }} (Observação da NFS-e., não-obrigatório)
- {{ rps.itens_servico[i].desconto }} (Valor do desconto do serviço (se houver))
- {{ rps.itens_servico[i].prof_parceiro }} (Objeto com informações de CNPJ, rz_social, inscrição municipal e percentual do valor repassado ao profissional parceiro (não-obrigatório))
- {{ rps.correcao }} (Objeto com informações para correção de NFS-e, não-obrigatório)