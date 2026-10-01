from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from datajustica.config import Settings
from datajustica.sources import isp_rj
from datajustica.storage.warehouse import get_observations, list_indicators, period_bounds


@pytest.fixture
def data_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    settings = Settings(data_dir=tmp_path)
    monkeypatch.setattr(isp_rj, "get_settings", lambda: settings)
    from datajustica.storage import warehouse

    monkeypatch.setattr(warehouse, "get_settings", lambda: settings)
    raw = settings.raw_dir
    raw.mkdir(parents=True)
    pd.DataFrame(
        [
            {
                "fmun_cod": 3300100,
                "fmun": "Angra dos Reis",
                "ano": 2024,
                "mes": 1,
                "mes_ano": "2024m01",
                "regiao": "Interior",
                "hom_doloso": 2,
                "fase": 3,
                "feminicidio": 0,
            },
            {
                "fmun_cod": 3300100,
                "fmun": "Angra dos Reis",
                "ano": 2024,
                "mes": 2,
                "mes_ano": "2024m02",
                "regiao": "Interior",
                "hom_doloso": 1,
                "fase": 3,
                "feminicidio": 1,
            },
        ]
    ).to_csv(
        raw / "isp_criminalidade_municipio_mensal.csv", sep=";", index=False, encoding="cp1252"
    )
    pd.DataFrame(
        [
            {
                "fmun_cod": 3300100,
                "fmun": "Angra dos Reis",
                "ano": 2024,
                "mes": 1,
                "mes_ano": "2024m01",
                "regiao": "Interior",
                "hom_doloso": 0.5,
                "fase": 3,
            },
            {
                "fmun_cod": 3300100,
                "fmun": "Angra dos Reis",
                "ano": 2024,
                "mes": 2,
                "mes_ano": "2024m02",
                "regiao": "Interior",
                "hom_doloso": 0.25,
                "fase": 3,
            },
        ]
    ).to_csv(
        raw / "isp_criminalidade_municipio_mensal_taxas.csv",
        sep=";",
        index=False,
        encoding="cp1252",
    )
    (raw / "isp_feminicidio_cisp_mensal.csv").write_text(
        '"CISP";"AISP";"RISP";"Município";"Mês";"Ano";"Feminicídio";'
        '"Tentativa de feminicídio";"Fase"\n'
        '1;5;1;"Angra dos Reis";"1";"2024";0;1;2\n'
        '1;5;1;"Angra dos Reis";"1";"2024";1;2;3\n',
        encoding="cp1252",
    )
    (raw / "manifest.json").write_text(
        json.dumps({"retrieved_at": "2026-09-30T12:00:00-03:00"}), encoding="utf-8"
    )
    return tmp_path


def test_etl_preserves_units_periods_and_provenance(data_root: Path) -> None:
    meta = isp_rj.build_warehouse()
    assert set(meta) == {"municipality_counts", "municipality_rates", "cisp_femicide"}
    rows = get_observations("municipality_counts", indicators=["hom_doloso"])
    assert rows["value"].tolist() == [2, 1]
    assert rows["geo_code"].tolist() == ["3300100", "3300100"]
    assert rows["frequency"].unique().tolist() == ["month"]
    assert meta["municipality_counts"]["source_url"].endswith("BaseMunicipioMensal.csv")


def test_nulls_are_not_changed_to_zero(data_root: Path) -> None:
    path = data_root / "raw/isp_criminalidade_municipio_mensal.csv"
    frame = pd.read_csv(path, sep=";", encoding="cp1252")
    frame.loc[0, "feminicidio"] = None
    frame.to_csv(path, sep=";", index=False, encoding="cp1252")
    isp_rj.build_warehouse()
    rows = get_observations("municipality_counts", indicators=["feminicidio"])
    assert rows["value"].tolist() == [1]


def test_cisp_keeps_latest_phase_and_location_detail(data_root: Path) -> None:
    isp_rj.build_warehouse()
    rows = get_observations("cisp_femicide")
    assert len(rows) == 2
    assert rows["value"].tolist() == [1, 2]
    assert rows["geo_level"].unique().tolist() == ["municipality_cisp"]
    assert rows["geo_name"].str.contains("Angra dos Reis").all()


def test_dimensions_and_period_bounds(data_root: Path) -> None:
    isp_rj.build_warehouse()
    assert {row["code"] for row in list_indicators("municipality_counts")} == {
        "feminicidio",
        "hom_doloso",
    }
    lo, hi = period_bounds("municipality_counts")
    assert lo.isoformat() == "2024-01-01"
    assert hi.isoformat() == "2024-02-01"
