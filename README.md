# DataJustiça · plataforma de pesquisa exploratória

Projeto Python para organizar e explorar séries abertas de segurança pública, com filtros por crime/indicador, município e período, comparação entre localidades e cenários de sensibilidade. A primeira base é real e delimitada: dados agregados do Instituto de Segurança Pública do Estado do Rio de Janeiro (ISP-RJ), capturados em **30/09/2026**.

> **Cobertura:** municípios do estado do Rio de Janeiro, em séries mensais. Não representa o Brasil. O ISP publica contagens municipais até 08/2026, taxas municipais até 12/2024 e feminicídio/tentativa por município e CISP até 07/2026. Semana não está disponível nessa base; o sistema não interpola mês em semana.

## O que inclui

- **Streamlit + Plotly:** filtros de série, indicador criminal, município/área, período e agregação mensal, trimestral ou anual.
- **DuckDB + Parquet:** consultas analíticas locais em formato colunar, sem exigir servidor de banco de dados.
- **FastAPI:** endpoints locais para observações, indicadores, áreas e metadados/proveniência.
- **ETL:** atualização dos três CSVs oficiais, validação de cabeçalhos, SHA-256, registro de data da coleta e geração dos Parquets.
- **Cenários de sensibilidade:** variações fornecidas pela pessoa usuária sobre a média recente. Não são previsões nem efeitos causais.
- **Dados incluídos:** snapshot oficial em `data/raw/`; a primeira execução funciona sem uma chamada inicial à internet.

Fontes, períodos, níveis geográficos e limitações estão em [`DATA_SOURCES.md`](DATA_SOURCES.md). Ocorrências são registros policiais e não equivalem a toda a incidência criminal. Outros estados serão conectores separados, com documentação de compatibilidade.

## Requisitos e instalação

Python 3.12 ou 3.13 é recomendado. O projeto declara suporte a Python 3.12 ou superior; o empacotamento tem como alvo conservador 3.12.

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev,research]"
```

## Rodar a aplicação

```bash
streamlit run src/datajustica/dashboard/app.py
```

A interface abre em `http://localhost:8501`. **Atualizar arquivos do ISP-RJ** baixa a versão mais recente e reconstrói a base. Também é possível usar a CLI:

```bash
datajustica refresh
datajustica build   # reconstrói só a partir de data/raw/
datajustica status  # mostra cobertura e hashes processados
```

## Publicar online

A interface pode ser hospedada no [Streamlit Community Cloud](https://share.streamlit.io/), ligado a este repositório do GitHub. O repositório inclui `requirements.txt` para instalar o pacote e suas dependências, além do ponto de entrada `streamlit_app.py`.

1. Entre no Streamlit Community Cloud com a conta GitHub que tem acesso administrativo ao repositório.
2. Selecione **Create app** e escolha `Ialisson/datajustica-2026`, branch `main` e arquivo `streamlit_app.py`.
3. Em **Advanced settings**, selecione Python 3.12 e publique.

O snapshot inicial fica versionado em `data/raw/`; os Parquets são criados automaticamente na primeira consulta. Depois da publicação, alterações enviadas à branch `main` atualizam o app. A aplicação é uma interface Streamlit; a API FastAPI permanece local e não deve ser exposta diretamente à internet.

## API local

```bash
uvicorn datajustica.api:app --host 127.0.0.1 --port 8000
```

- `GET /health`
- `GET /v1/datasets`
- `GET /v1/indicators?dataset=municipality_counts`
- `GET /v1/areas?dataset=municipality_counts`
- `GET /v1/observations?dataset=municipality_counts&indicator=estupro&start=2024-01-01&end=2026-08-01`
- `GET /docs` para OpenAPI

A API é local e sem autenticação. Não a exponha diretamente à internet.

## Docker

```bash
docker compose up --build
```

A aplicação fica em `http://localhost:8501`; o volume `./data` preserva as atualizações no host.

## Verificação e pesquisa

```bash
pytest
ruff check .
```

Os extras `research` incluem JupyterLab, statsmodels e scikit-learn para análises posteriores sobre as tabelas rastreáveis. Nenhum modelo preditivo ou desenho causal é declarado como validado neste projeto.

## Arquitetura

```text
ISP-RJ (CSV oficial)
        │
        ▼
sources/isp_rj.py ── valida cabeçalhos + calcula SHA-256
        │
        ▼
data/raw/ (snapshot rastreável)
        │
        ▼
transformação pandas ──> data/processed/*.parquet
                                      │
                    ┌─────────────────┴─────────────────┐
                    ▼                                   ▼
          dashboard Streamlit                    API FastAPI
                    └──────── consultas DuckDB ────────┘
```

Cada observação guarda fonte, período, nível geográfico, indicador e unidade. Dados brutos versionados servem como snapshot reproduzível; o ETL recria os Parquets derivados.

## Expansões recomendadas

1. Conector Sinesp/MJSP para cobertura nacional e por UF/município, depois de validar o dicionário, o formato e a atualização de cada recurso.
2. Conector SIM/DataSUS para mortalidade segundo CID-10, sem equiparar automaticamente homicídio de mulher a feminicídio jurídico.
3. Conectores de outros institutos estaduais como fontes isoladas; não concatenar categorias sem harmonização auditável.
4. Denominadores anuais do IBGE para taxas calculadas pelo projeto, com versão e ano de referência registrados.
5. Frequência semanal somente se uma fonte oficial compatível a publicar.

## Licença e atribuição

Atribuição dos dados: Instituto de Segurança Pública do Estado do Rio de Janeiro (ISP-RJ), ISPdados Abertos. Links, arquivos e datas constam em `DATA_SOURCES.md`. Confirme as condições de reutilização indicadas pelo publicador antes de redistribuir. O repositório recebido não continha licença de software; este trabalho não presume um novo termo.
