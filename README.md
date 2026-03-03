# DataJustiça 2026 — Ciência de Dados & Justiça Social

> Scrollytelling narrativo + visualização geoespacial + IA conversacional aplicados ao estudo do racismo estrutural e da violência contra a mulher no Brasil.

![DataJustiça 2026](https://img.shields.io/badge/versão-2026-f59e0b?style=flat-square)
![HTML](https://img.shields.io/badge/HTML-single--file-60a5fa?style=flat-square)
![D3.js](https://img.shields.io/badge/D3.js-7.8.5-ef4444?style=flat-square)
![Chart.js](https://img.shields.io/badge/Chart.js-4.4.1-4ade80?style=flat-square)
![Claude API](https://img.shields.io/badge/Claude-API-f59e0b?style=flat-square)
![GitHub Pages](https://img.shields.io/badge/GitHub_Pages-ready-14b8a6?style=flat-square)

---

## 🔍 Sobre o Projeto

Este projeto aplica técnicas modernas de ciência de dados para analisar duas das questões sociais mais urgentes do Brasil:

- **Tema 1 — Racismo Estrutural:** Como o racismo se manifesta em renda, educação, saúde e justiça — e como dados podem orientar políticas eficazes.
- **Tema 2 — Violência contra a Mulher:** Padrões históricos, impacto da pandemia, perfil das vítimas e eficácia de intervenções.

---

## ✨ Funcionalidades

| Feature | Tecnologia | Descrição |
|---|---|---|
| **Scrollytelling** | CSS + IntersectionObserver | Narrativa guiada — gráficos mudam conforme o scroll |
| **Mapa Geoespacial** | D3.js + API IBGE | 27 estados com IVM e IDR interativos, tooltip detalhado |
| **IA Conversacional** | Claude API (Anthropic) | Perguntas em linguagem natural sobre os dados do projeto |
| **Visualizações** | Chart.js 4.4 | 8 gráficos — linha, barra, doughnut, radar, scatter |
| **Barra de Progresso** | CSS + JS | Indicador de leitura no topo da página |
| **Design Dark Editorial** | CSS puro | Tipografia Syne + DM Sans + JetBrains Mono |

---

## 📊 Modelos e Técnicas Utilizadas

```
Análise Exploratória (EDA)
├── Estatísticas descritivas por grupo racial
├── Heatmap de correlação de Pearson
└── Decomposição de séries temporais

Modelagem Preditiva
├── Regressão Linear Múltipla (β = −0,28, p < 0,001)
├── ARIMA(2,1,2) — projeção de feminicídios
├── Random Forest (AUC-ROC = 0,84 | F1 = 0,79)
└── Diferença em Diferenças — impacto causal das cotas

Clustering & Redução Dimensional
├── K-Means (k=5, Silhouette Score = 0,61)
├── PCA — PC1 explica 67% da variância
└── Chow Test — quebra estrutural pós-2015
```

---

## 📁 Estrutura do Repositório

```
datajustica-2026/
├── index.html          # Versão 2026 — Scrollytelling + Mapa + IA
├── dashboard-v1.html   # Versão 2024 — Dashboard clássico com abas
└── README.md
```

---

## 🚀 Como Usar

### Opção 1 — Abrir localmente
```bash
git clone https://github.com/SEU_USUARIO/datajustica-2026.git
cd datajustica-2026
# Abra index.html no navegador
open index.html   # macOS
xdg-open index.html  # Linux
```

### Opção 2 — GitHub Pages (recomendado)
1. No repositório, vá em **Settings → Pages**
2. Source: **Deploy from a branch**
3. Branch: `main` → pasta: `/ (root)`
4. Aguarde ~1 min e acesse `https://SEU_USUARIO.github.io/datajustica-2026`

> **Nota sobre a IA:** Para usar o chat conversacional, a página deve ser servida por um servidor web (GitHub Pages funciona). Ao abrir como arquivo local (`file://`), o navegador pode bloquear a chamada à API.

---

## 🗺️ Mapa — Dados por Estado

O mapa carrega o GeoJSON oficial do IBGE via API em tempo real. Caso não haja conexão, o ranking lateral permanece funcional.

**Índices utilizados:**

- **IVM** (Índice de Violência contra a Mulher): composto por feminicídios (40%) + violência doméstica (30%) + estupros (20%) + subnotificação estimada (10%)
- **IDR** (Índice de Desigualdade Racial): composto por renda, escolaridade, encarceramento e acesso à saúde

---

## 📚 Fontes dos Dados

| Fonte | Dados utilizados |
|---|---|
| **IBGE / PNAD Contínua** | Renda, escolaridade, mercado de trabalho (2012–2023) |
| **FBSP / Atlas da Violência 2023** | Feminicídios, violência doméstica, IVM por estado |
| **DataSUS / SINAN** | Mortalidade materna, agravos de notificação |
| **INEP** | Censo da Educação Superior (2012–2023) |
| **MDH / Ligue 180** | Chamadas à central, sazonalidade (2018–2022) |
| **IPEA** | Indicadores de pobreza e desigualdade racial |

---

## 📖 Referências Bibliográficas

- Cerqueira et al. (2019). *"O Jogo dos Sete Erros: Avaliação de Impacto da Lei Maria da Penha."* IPEA.
- FBSP. *Atlas da Violência 2023.* Fórum Brasileiro de Segurança Pública / IPEA.
- IBGE. *Pesquisa Nacional por Amostra de Domicílios Contínua (PNAD) 2012–2023.*
- MDH. *Relatório Anual Central Ligue 180, 2022.*

---

## 🛠️ Tecnologias

- **D3.js 7.8.5** — visualização geoespacial e mapa do Brasil
- **Chart.js 4.4.1** — gráficos interativos
- **Anthropic Claude API** — IA conversacional especializada
- **Google Fonts** — Syne, DM Sans, JetBrains Mono
- **CSS puro** — animações, scrollytelling, dark theme

---

## 📄 Licença

MIT License — livre para uso educacional e acadêmico.

---

*Projeto de Ciência de Dados · 2026 · DataJustiça*
