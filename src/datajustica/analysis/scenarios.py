from __future__ import annotations

from collections.abc import Sequence

import pandas as pd


def aggregate_period(frame: pd.DataFrame, frequency: str) -> pd.DataFrame:
    """Aggregate observed monthly rows to month, quarter or year; never upsample."""
    if frequency not in {"month", "quarter", "year"}:
        raise ValueError("Frequência suportada: month, quarter ou year")
    result = frame.copy()
    result["period_start"] = pd.to_datetime(result["period_start"])
    if frequency == "quarter":
        result["period_start"] = result["period_start"].dt.to_period("Q").dt.start_time
    elif frequency == "year":
        result["period_start"] = result["period_start"].dt.to_period("Y").dt.start_time
    return result.groupby(["period_start", "geo_name"], as_index=False)["value"].sum()


def sensitivity_scenarios(
    frame: pd.DataFrame, variations_percent: Sequence[float], *, months: int = 12
) -> pd.DataFrame:
    """Apply user-defined percentages to the recent observed monthly mean, not a forecast."""
    if not variations_percent:
        raise ValueError("Informe ao menos uma premissa de cenário")
    if months < 1:
        raise ValueError("months deve ser positivo")
    if frame.empty:
        raise ValueError("Não há observações no recorte")
    if "unit" in frame and frame["unit"].nunique() != 1:
        raise ValueError("Não combine unidades diferentes em um mesmo cenário")
    if "unit" in frame and frame["unit"].iloc[0] != "occurrences":
        raise ValueError("Cenários de sensibilidade são limitados a contagens")
    monthly = (
        frame.groupby("period_start", as_index=False)["value"].sum().sort_values("period_start")
    )
    monthly = monthly.tail(months)
    if len(monthly) < months:
        raise ValueError(f"São necessários pelo menos {months} meses observados")
    baseline = float(monthly["value"].mean())
    if baseline < 0:
        raise ValueError("A média de referência não pode ser negativa")
    return pd.DataFrame(
        {
            "variation_percent": list(variations_percent),
            "baseline_mean": baseline,
            "scenario_mean": [baseline * (1 + value / 100) for value in variations_percent],
        }
    )
