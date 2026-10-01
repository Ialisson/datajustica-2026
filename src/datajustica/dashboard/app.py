from __future__ import annotations

from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from datajustica.analysis.scenarios import aggregate_period, sensitivity_scenarios
from datajustica.sources.catalog import SOURCES
from datajustica.sources.isp_rj import build_warehouse, download_latest
from datajustica.storage.warehouse import (
    DATASETS,
    get_observations,
    indicator_label,
    list_areas,
    list_indicators,
    metadata,
    period_bounds,
)

st.set_page_config(page_title="DataJustiça · pesquisa criminal", page_icon="⚖️", layout="wide")


@st.cache_data(ttl=300, show_spinner=False)
def dimensions(dataset: str):
    return list_indicators(dataset), list_areas(dataset), period_bounds(dataset)


def summary(frame: pd.DataFrame, dataset: str) -> None:
    if frame.empty:
        st.info("Nenhuma observação nesse recorte. Amplie o período ou altere os filtros.")
        return
    latest = frame["period_start"].max()
    value = frame.loc[frame["period_start"] == latest, "value"]
    unique_areas = frame["geo_name"].nunique()
    if dataset == "municipality_rates" and unique_areas > 1:
        st.caption(
            "Taxas municipais não são somadas nem promediadas; "
            "examine cada município separadamente."
        )
        st.metric("Municípios no recorte", unique_areas)
        return
    metric_value = (
        float(frame["value"].sum())
        if frame["unit"].iloc[0] == "occurrences"
        else float(value.iloc[0])
    )
    left, middle, right = st.columns(3)
    left.metric("Observações", f"{len(frame):,}".replace(",", "."))
    middle.metric(
        "Valor no recorte",
        f"{metric_value:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
    )
    right.metric("Último mês disponível", latest.strftime("%m/%Y"))


def scenario_analysis(frame: pd.DataFrame) -> None:
    st.subheader("Cenários hipotéticos")
    st.caption(
        "Variações aritméticas sobre a média observada nos 12 meses mais recentes. "
        "São premissas editáveis: "
        "não representam previsão, contrafactual, avaliação de política nem efeito causal."
    )
    if frame.empty or frame["unit"].iloc[0] != "occurrences":
        st.info("Cenários aritméticos estão disponíveis para contagens, não para taxas.")
        return
    try:
        scenarios = sensitivity_scenarios(frame, [-10.0, 0.0, 10.0])
    except ValueError as exc:
        st.info(str(exc))
        return
    baseline = float(scenarios["baseline_mean"].iloc[0])
    columns = st.columns(3)
    assumptions = [
        columns[0].number_input("Cenário A · variação (%)", -100.0, 300.0, -10.0, 5.0),
        columns[1].number_input("Cenário B · variação (%)", -100.0, 300.0, 0.0, 5.0),
        columns[2].number_input("Cenário C · variação (%)", -100.0, 300.0, 10.0, 5.0),
    ]
    scenarios = sensitivity_scenarios(frame, assumptions).assign(
        scenario_name=[
            f"Cenário {name} ({value:+.0f}%)"
            for name, value in zip("ABC", assumptions, strict=True)
        ]
    )
    st.caption(
        f"Referência: média de {baseline:,.1f} ocorrências por mês nos 12 meses mais recentes."
    )
    st.plotly_chart(
        px.bar(
            scenarios,
            x="scenario_name",
            y="scenario_mean",
            color="scenario_name",
            labels={"scenario_name": "Cenário", "scenario_mean": "Média mensal hipotética"},
        ),
        use_container_width=True,
    )


def main() -> None:
    st.title("DataJustiça · exploração de dados criminais")
    st.warning(
        "**Cobertura inicial:** registros mensais oficiais do ISP-RJ. "
        "Os dados não representam todo o Brasil. "
        "Esta fonte publica dados mensais; não há observações semanais para este recorte. "
        "Registros policiais "
        "não representam toda a incidência criminal."
    )
    with st.sidebar:
        st.header("Fontes e filtros")
        if st.button("Atualizar arquivos do ISP-RJ", use_container_width=True):
            try:
                with st.spinner("Baixando, validando e reconstruindo as séries..."):
                    download_latest()
                    build_warehouse()
                dimensions.clear()
                st.success("Arquivos oficiais atualizados e base analítica reconstruída.")
                st.rerun()
            except Exception as exc:
                st.error(f"A atualização falhou; a cópia anterior foi mantida. Detalhe: {exc}")
        dataset = st.selectbox(
            "Série",
            list(DATASETS),
            format_func=lambda key: f"{DATASETS[key][0]} ({DATASETS[key][1]})",
        )
        try:
            indicators, all_areas, bounds = dimensions(dataset)
        except Exception as exc:
            st.error(f"Não foi possível carregar os dados: {exc}")
            st.stop()
        indicator_codes = [item["code"] for item in indicators]
        preferred = "feminicidio" if "feminicidio" in indicator_codes else indicator_codes[0]
        indicator = st.selectbox(
            "Crime / indicador",
            indicator_codes,
            index=indicator_codes.index(preferred),
            format_func=indicator_label,
        )
        areas = st.multiselect("Municípios / áreas (vazio = todos)", all_areas)
        default_start = max(bounds[0], date(bounds[1].year - 4, bounds[1].month, 1))
        dates = st.date_input(
            "Período",
            value=(default_start, bounds[1]),
            min_value=bounds[0],
            max_value=bounds[1],
            format="DD/MM/YYYY",
        )
        granularity = st.selectbox("Agregação temporal", ["Mensal", "Trimestral", "Anual"])
        st.caption(
            "Semanal: não disponível nessa fonte; não desagregamos nem interpolamos os meses."
        )

    if not isinstance(dates, tuple) or len(dates) != 2:
        st.info("Selecione uma data inicial e uma final para continuar.")
        st.stop()
    start, end = dates
    if start > end:
        st.error("A data inicial precisa ser anterior à data final.")
        st.stop()
    frame = get_observations(
        dataset, indicators=[indicator], areas=areas or None, start=start, end=end
    )
    frame["period_start"] = pd.to_datetime(frame["period_start"])
    source_key = "isp_rj_femicide_cisp" if dataset == "cisp_femicide" else "isp_rj_municipal"
    source = SOURCES[source_key]
    st.subheader(indicator_label(indicator))
    unit = frame["unit"].iloc[0] if not frame.empty else "sem observações"
    st.caption(f"Fonte: {source.publisher} · {DATASETS[dataset][1]} · unidade: {unit}")
    if dataset == "municipality_rates" and not areas:
        st.info(
            "Selecione município(s) para consultar as taxas publicadas. "
            "A soma ou média simples não é uma taxa estadual."
        )
        st.stop()
    summary(frame, dataset)
    if frame.empty:
        return
    frequency = {"Mensal": "month", "Trimestral": "quarter", "Anual": "year"}[granularity]
    compare = aggregate_period(frame, frequency)
    if len(areas) <= 1 and dataset != "municipality_rates":
        series = compare.groupby("period_start", as_index=False)["value"].sum()
        title = (
            "Total das áreas selecionadas" if areas else "Total estadual dos municípios publicados"
        )
        st.plotly_chart(
            px.line(series, x="period_start", y="value", markers=True, title=title),
            use_container_width=True,
        )
    elif len(areas) <= 6:
        st.plotly_chart(
            px.line(
                compare,
                x="period_start",
                y="value",
                color="geo_name",
                markers=True,
                title="Comparação entre localidades",
            ),
            use_container_width=True,
        )
    else:
        st.info(
            "Selecione até seis áreas para comparar as séries individuais; "
            "o ranking abaixo abrange o recorte inteiro."
        )
    if dataset == "municipality_counts":
        top = frame.groupby("geo_name", as_index=False)["value"].sum().nlargest(20, "value")
        st.plotly_chart(
            px.bar(
                top.sort_values("value"),
                x="value",
                y="geo_name",
                orientation="h",
                title="Maiores contagens no período",
            ),
            use_container_width=True,
        )
    if dataset != "municipality_rates":
        scenario_analysis(frame)
    with st.expander("Tabela de observações", expanded=False):
        view = frame.copy()
        view["indicator_label"] = view["indicator_code"].map(indicator_label)
        st.dataframe(view, use_container_width=True, hide_index=True)
    with st.expander("Qualidade, definições e proveniência"):
        st.json(metadata().get(dataset, {}))
        st.markdown(f"[Página oficial da fonte]({source.landing_page})")
        st.markdown(source.caveat)
        st.markdown("Variação temporal e cenários hipotéticos não demonstram causa.")
    st.caption(
        "Ferramenta exploratória de pesquisa. Verifique dicionário, revisões e notas "
        "metodológicas da fonte antes de citar."
    )


if __name__ == "__main__":
    main()
