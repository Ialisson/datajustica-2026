# Fontes, cobertura e proveniência

## Snapshot incluído

Os arquivos abaixo foram baixados dos CSVs oficiais do ISP-RJ em **30 de setembro de 2026**. `data/raw/manifest.json` registra URL, tamanho e SHA-256. `data/processed/manifest.json`, criado por `datajustica build`, registra a contagem de linhas e o intervalo processado.

| Arquivo | Conteúdo / geografia | Período no snapshot |
|---|---|---|
| `isp_criminalidade_municipio_mensal.csv` | Contagens de indicadores por município do RJ e mês | jan/2014–ago/2026 |
| `isp_criminalidade_municipio_mensal_taxas.csv` | Taxas por 100 mil habitantes, conforme cálculo/publicação do ISP | jan/2014–dez/2024 |
| `isp_feminicidio_cisp_mensal.csv` | Feminicídio/tentativa por município × CISP | nov/2016–jul/2026 |

A base criminal municipal tem 13.984 linhas wide, convertidas pelo ETL para observações longas. As taxas têm janela menor e não são preenchidas com contagens. No arquivo CISP o ETL mantém a fase administrativa mais alta para município × CISP × mês.

## Links oficiais

- [Estatísticas de Segurança Pública — ISPdados Abertos](https://www.ispdados.rj.gov.br/estatistica.html)
- [Crimes contra a vida — ISPdados Abertos](https://www.ispdados.rj.gov.br/CrimesVida.html)
- [CSV: criminalidade municipal mensal](https://www.ispdados.rj.gov.br/Arquivos/BaseMunicipioMensal.csv)
- [CSV: taxas municipais mensais](https://www.ispdados.rj.gov.br/Arquivos/BaseMunicipioTaxaMes.csv)
- [CSV: feminicídio mensal por CISP](https://www.ispdados.rj.gov.br/Arquivos/BaseFeminicidioEvolucaoMensalCisp.csv)

O botão na aplicação e `datajustica refresh` baixam novamente os arquivos, verificam cabeçalhos antes de substituir o snapshot, registram hashes e a hora local da coleta. A data de download não é a data da última atualização do ISP; o intervalo observado de cada arquivo é a referência no aplicativo.

## Limites de interpretação

- A cobertura inicial é **apenas o estado do Rio de Janeiro**.
- Os dados são registros administrativos; subnotificação, classificação, mudanças de procedimento e revisões afetam as séries.
- Uma contagem maior não prova uma taxa populacional maior. A taxa publicada tem seu próprio denominador/método e não é somada ou promediada entre municípios.
- A periodicidade da origem é mensal. Agregações trimestrais e anuais somam meses observados; semana/dia não estão disponíveis nem são estimados.
- Indicadores podem se sobrepor. Não some totais e componentes. O usuário seleciona uma natureza/indicador por vez.
- CISP é uma unidade policial administrativa, não coordenada do evento nem necessariamente equivalente a limite municipal.
- Valor ausente permanece ausente; não é convertido em zero.
- Cenários alteram aritmeticamente uma média recente conforme percentuais inseridos pela pessoa usuária. Não são forecast, avaliação causal nem contrafactual.

## Fontes para expansão (ainda não integradas)

- [Sinesp/MJSP — Ocorrências Criminais](https://dados.mj.gov.br/dataset/sistema-nacional-de-estatisticas-de-seguranca-publica): indicadores agregados estaduais/nacionais e recursos municipais; formato, data e cobertura precisam ser validados por arquivo. O catálogo inclui alguns arquivos municipais cuja publicação é mais antiga que a periodicidade mensal declarada para o sistema.
- [SIM/DataSUS](https://dadosabertos.saude.gov.br/dataset/sim): microdados de mortalidade por município e causa CID-10. Óbito por causa não classifica automaticamente feminicídio jurídico.
- [IBGE — API de localidades](https://servicodados.ibge.gov.br/api/docs/localidades): referência de códigos territoriais.
- [IBGE — estimativas de população](https://www.ibge.gov.br/estatisticas/sociais/populacao/9103-estimativas-de-population.html): possível denominador anual; registrar versão e ano se utilizado.

O Sinesp VDE recebe séries mensais, mas cada indicador deve manter sua fonte, data de extração e ressalvas estaduais. Nenhum desses conjuntos nacionais foi unido ao snapshot ISP-RJ até validar formato, dicionário e comparabilidade.
