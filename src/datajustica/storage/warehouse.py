from __future__ import annotations

import json
from datetime import date
from typing import Literal

import duckdb
import pandas as pd

from datajustica.config import get_settings

DatasetId = Literal["municipality_counts", "municipality_rates", "cisp_femicide"]
DATASETS: dict[str, tuple[str, str]] = {
    "municipality_counts": ("Ocorrências por município · mensal", "2014–2026 · até agosto"),
    "municipality_rates": ("Taxas por 100 mil habitantes · mensal", "2014–2024 · publicação ISP"),
    "cisp_femicide": (
        "Feminicídio e tentativa · município × CISP · mensal",
        "2016–2026 · até julho",
    ),
}


def parquet_path(dataset_id: str):
    if dataset_id not in DATASETS:
        raise ValueError(f"Dataset não reconhecido: {dataset_id}")
    path = get_settings().processed_dir / f"{dataset_id}.parquet"
    if not path.is_file():
        from datajustica.sources.isp_rj import build_warehouse

        build_warehouse()
    if not path.is_file():
        raise FileNotFoundError("Dados processados ausentes; execute `datajustica build`.")
    return path


def _query(sql: str, params: list[object] | None = None) -> pd.DataFrame:
    with duckdb.connect(database=":memory:") as connection:
        return connection.execute(sql, params or []).df()


def list_indicators(dataset_id: str) -> list[dict[str, str]]:
    path = parquet_path(dataset_id)
    frame = _query("SELECT DISTINCT indicator_code FROM read_parquet(?) ORDER BY 1", [str(path)])
    return [
        {"code": code, "label": indicator_label(code)} for code in frame["indicator_code"].tolist()
    ]


def list_areas(dataset_id: str) -> list[str]:
    path = parquet_path(dataset_id)
    return _query("SELECT DISTINCT geo_name FROM read_parquet(?) ORDER BY 1", [str(path)])[
        "geo_name"
    ].tolist()


def period_bounds(dataset_id: str) -> tuple[date, date]:
    frame = _query(
        "SELECT min(period_start) AS lo, max(period_start) AS hi FROM read_parquet(?)",
        [str(parquet_path(dataset_id))],
    )
    return frame.loc[0, "lo"].date(), frame.loc[0, "hi"].date()


def get_observations(
    dataset_id: str,
    *,
    indicators: list[str] | None = None,
    areas: list[str] | None = None,
    start: date | None = None,
    end: date | None = None,
) -> pd.DataFrame:
    clauses: list[str] = []
    params: list[object] = [str(parquet_path(dataset_id))]
    for column, values in (("indicator_code", indicators), ("geo_name", areas)):
        if values:
            clauses.append(column + " IN (" + ",".join("?" for _ in values) + ")")
            params.extend(values)
    if start:
        clauses.append("period_start >= ?")
        params.append(start)
    if end:
        clauses.append("period_start <= ?")
        params.append(end)
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    return _query(
        "SELECT * FROM read_parquet(?)" + where + " ORDER BY period_start, geo_name", params
    )


def metadata() -> dict[str, dict[str, object]]:
    path = get_settings().processed_dir / "manifest.json"
    if not path.is_file():
        from datajustica.sources.isp_rj import build_warehouse

        build_warehouse()
    return json.loads(path.read_text(encoding="utf-8"))


def indicator_label(code: str) -> str:
    known = {
        "hom_doloso": "Homicídio doloso",
        "lesao_corp_morte": "Lesão corporal seguida de morte",
        "latrocinio": "Latrocínio",
        "cvli": "Crimes violentos letais intencionais (CVLI)",
        "hom_por_interv_policial": "Morte por intervenção policial",
        "feminicidio": "Feminicídio",
        "tentativa_feminicidio": "Tentativa de feminicídio",
        "lesao_corp_dolosa": "Lesão corporal dolosa",
        "estupro": "Estupro",
        "roubo_rua": "Roubo de rua",
        "roubo_veiculo": "Roubo de veículo",
        "roubo_carga": "Roubo de carga",
        "total_roubos": "Total de roubos (categoria agregada pelo ISP)",
        "total_furtos": "Total de furtos (categoria agregada pelo ISP)",
        "estelionato": "Estelionato",
        "ameaca": "Ameaça",
        "registro_ocorrencias": "Registros de ocorrência (total)",
        "tentativa_de_feminicidio": "Tentativa de feminicídio",
    }
    return known.get(code, code.replace("_", " ").capitalize())
