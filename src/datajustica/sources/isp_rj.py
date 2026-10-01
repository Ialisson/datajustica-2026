from __future__ import annotations

import csv
import hashlib
import json
import os
import tempfile
import unicodedata
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
import pandas as pd

from datajustica.config import get_settings

FILES = {
    "isp_criminalidade_municipio_mensal.csv": "https://www.ispdados.rj.gov.br/Arquivos/BaseMunicipioMensal.csv",
    "isp_criminalidade_municipio_mensal_taxas.csv": "https://www.ispdados.rj.gov.br/Arquivos/BaseMunicipioTaxaMes.csv",
    "isp_feminicidio_cisp_mensal.csv": "https://www.ispdados.rj.gov.br/Arquivos/BaseFeminicidioEvolucaoMensalCisp.csv",
}
REQUIRED = {
    "isp_criminalidade_municipio_mensal.csv": {"fmun_cod", "fmun", "ano", "mes", "hom_doloso"},
    "isp_criminalidade_municipio_mensal_taxas.csv": {
        "fmun_cod",
        "fmun",
        "ano",
        "mes",
        "hom_doloso",
    },
    "isp_feminicidio_cisp_mensal.csv": {"cisp", "municipio", "mes", "ano", "feminicidio"},
}


def _fold(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().casefold()
    return " ".join(text.split())


def _header(path) -> set[str]:
    with path.open(encoding="cp1252", newline="") as stream:
        try:
            fields = next(csv.reader(stream, delimiter=";"))
        except StopIteration as exc:
            raise ValueError(f"Arquivo vazio: {path.name}") from exc
    return {_fold(field).replace(" ", "_").strip('"') for field in fields}


def download_latest(*, timeout: float = 120.0) -> dict[str, object]:
    """Fetch all ISP files to temporary paths; validate before replacing the local snapshot."""
    raw_dir = get_settings().raw_dir
    raw_dir.mkdir(parents=True, exist_ok=True)
    temporary: dict[str, Path] = {}
    file_manifest: dict[str, dict[str, str | int]] = {}
    try:
        with httpx.Client(
            timeout=timeout, follow_redirects=True, headers={"User-Agent": "DataJustica/0.2"}
        ) as client:
            for filename, url in FILES.items():
                fd, temp_name = tempfile.mkstemp(prefix="datajustica-", suffix=".csv", dir=raw_dir)
                os.close(fd)
                temp_path = Path(temp_name)
                temporary[filename] = temp_path
                digest, size = hashlib.sha256(), 0
                with client.stream("GET", url) as response:
                    response.raise_for_status()
                    with temp_path.open("wb") as output:
                        for chunk in response.iter_bytes():
                            output.write(chunk)
                            digest.update(chunk)
                            size += len(chunk)
                if size < 100:
                    raise ValueError(f"Resposta pequena demais para um CSV: {filename}")
                missing = REQUIRED[filename] - _header(temp_path)
                if missing:
                    raise ValueError(
                        f"Cabeçalho inesperado em {filename}; faltam {sorted(missing)}"
                    )
                file_manifest[filename] = {"url": url, "sha256": digest.hexdigest(), "bytes": size}
        retrieved_at = datetime.now(ZoneInfo("America/Sao_Paulo")).isoformat(timespec="seconds")
        for filename, temp_path in temporary.items():
            temp_path.replace(raw_dir / filename)
        record = {"retrieved_at": retrieved_at, "publisher": "ISP-RJ", "files": file_manifest}
        manifest_path = raw_dir / "manifest.json"
        temp_manifest = manifest_path.with_suffix(".json.tmp")
        temp_manifest.write_text(
            json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        temp_manifest.replace(manifest_path)
        return record
    except Exception:
        for path in temporary.values():
            path.unlink(missing_ok=True)
        raise


def _read_csv(filename: str) -> pd.DataFrame:
    path = get_settings().raw_dir / filename
    if not path.is_file():
        raise FileNotFoundError(f"Arquivo de origem ausente: {path}. Execute `datajustica update`.")
    return pd.read_csv(
        path, sep=";", encoding="cp1252", decimal=",", dtype_backend="numpy_nullable"
    )


def _long_municipal(filename: str, dataset_id: str) -> pd.DataFrame:
    frame = _read_csv(filename)
    frame.columns = [str(col).strip().casefold() for col in frame.columns]
    required = {"fmun_cod", "fmun", "ano", "mes", "fase"}
    if missing := required - set(frame.columns):
        raise ValueError(f"Colunas obrigatórias ausentes em {filename}: {sorted(missing)}")
    frame["geo_code"] = frame["fmun_cod"].astype("string").str.strip().str.zfill(7)
    frame["geo_name"] = frame["fmun"].astype("string").str.strip()
    frame["year"] = pd.to_numeric(frame["ano"], errors="coerce")
    frame["month"] = pd.to_numeric(frame["mes"], errors="coerce")
    frame["phase"] = pd.to_numeric(frame["fase"], errors="coerce").fillna(0)
    frame = frame.dropna(subset=["year", "month", "geo_code", "geo_name"])
    frame["period_start"] = pd.to_datetime(
        {"year": frame["year"].astype(int), "month": frame["month"].astype(int), "day": 1},
        errors="coerce",
    )
    metadata = {"fmun_cod", "fmun", "ano", "mes", "mes_ano", "regiao", "fase"}
    internals = {"geo_code", "geo_name", "year", "month", "phase", "period_start"}
    indicators = [col for col in frame.columns if col not in metadata | internals]
    for col in indicators:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    long = frame.melt(
        id_vars=["geo_code", "geo_name", "year", "month", "period_start", "phase"],
        value_vars=indicators,
        var_name="indicator_code",
        value_name="value",
    ).dropna(subset=["period_start", "value"])
    long = long[long["value"] >= 0].copy()
    long["source_id"] = "isp_rj_municipal"
    long["dataset_id"] = dataset_id
    long["geo_level"] = "municipality"
    long["uf"] = "RJ"
    long["unit"] = "rate_per_100k" if dataset_id == "municipality_rates" else "occurrences"
    long["frequency"] = "month"
    return long.drop(columns="phase")


def _cisp_femicide(municipality_codes: dict[str, str]) -> pd.DataFrame:
    frame = _read_csv("isp_feminicidio_cisp_mensal.csv")
    frame.columns = [_fold(col).replace(" ", "_") for col in frame.columns]
    required = {
        "cisp",
        "municipio",
        "mes",
        "ano",
        "feminicidio",
        "tentativa_de_feminicidio",
        "fase",
    }
    if missing := required - set(frame.columns):
        raise ValueError(f"Colunas ausentes no CSV de feminicídio por CISP: {sorted(missing)}")
    frame["municipality_key"] = frame["municipio"].map(_fold)
    frame["cisp"] = frame["cisp"].astype("string").str.strip()
    frame["year"] = pd.to_numeric(frame["ano"], errors="coerce")
    frame["month"] = pd.to_numeric(frame["mes"], errors="coerce")
    frame["phase"] = pd.to_numeric(frame["fase"], errors="coerce").fillna(0)
    for col in ("feminicidio", "tentativa_de_feminicidio"):
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    frame = frame.dropna(subset=["year", "month", "municipio", "cisp"])
    frame = frame.sort_values("phase").drop_duplicates(
        subset=["municipality_key", "cisp", "year", "month"], keep="last"
    )
    frame["period_start"] = pd.to_datetime(
        {"year": frame["year"].astype(int), "month": frame["month"].astype(int), "day": 1},
        errors="coerce",
    )
    frame["geo_code"] = frame.apply(
        lambda row: f"{municipality_codes.get(row['municipality_key'], 'unknown')}:{row['cisp']}",
        axis=1,
    )
    frame["geo_name"] = (
        frame["municipio"].astype("string") + " · CISP " + frame["cisp"].astype("string")
    )
    long = frame.melt(
        id_vars=["geo_code", "geo_name", "year", "month", "period_start"],
        value_vars=["feminicidio", "tentativa_de_feminicidio"],
        var_name="indicator_code",
        value_name="value",
    ).dropna(subset=["period_start", "value"])
    long = long[long["value"] >= 0].copy()
    long["source_id"] = "isp_rj_femicide_cisp"
    long["dataset_id"] = "cisp_femicide"
    long["geo_level"] = "municipality_cisp"
    long["uf"] = "RJ"
    long["unit"] = "occurrences"
    long["frequency"] = "month"
    return long


def _metadata(frame: pd.DataFrame, dataset_id: str, filename: str) -> dict[str, object]:
    raw = get_settings().raw_dir / filename
    digest = hashlib.sha256(raw.read_bytes()).hexdigest()
    manifest = get_settings().raw_dir / "manifest.json"
    retrieved = "snapshot packaged with project; consult DATA_SOURCES.md"
    if manifest.is_file():
        retrieved = json.loads(manifest.read_text(encoding="utf-8")).get("retrieved_at", retrieved)
    return {
        "dataset_id": dataset_id,
        "source_file": filename,
        "source_url": FILES[filename],
        "retrieved_at": retrieved,
        "sha256": digest,
        "row_count": int(len(frame)),
        "period_start": str(frame["period_start"].min().date()),
        "period_end": str(frame["period_start"].max().date()),
        "frequency": "month",
    }


def build_warehouse() -> dict[str, dict[str, object]]:
    """Normalize the public CSVs and write compressed, provenance-bearing Parquet tables."""
    settings = get_settings()
    settings.processed_dir.mkdir(parents=True, exist_ok=True)
    counts = _long_municipal("isp_criminalidade_municipio_mensal.csv", "municipality_counts")
    rates = _long_municipal("isp_criminalidade_municipio_mensal_taxas.csv", "municipality_rates")
    municipality_codes = {
        _fold(name): str(code)
        for code, name in counts[["geo_code", "geo_name"]]
        .drop_duplicates()
        .itertuples(index=False, name=None)
    }
    cisp = _cisp_femicide(municipality_codes)
    datasets = {
        "municipality_counts": (counts, "isp_criminalidade_municipio_mensal.csv"),
        "municipality_rates": (rates, "isp_criminalidade_municipio_mensal_taxas.csv"),
        "cisp_femicide": (cisp, "isp_feminicidio_cisp_mensal.csv"),
    }
    result: dict[str, dict[str, object]] = {}
    for dataset_id, (frame, filename) in datasets.items():
        frame = frame.sort_values(["period_start", "geo_name", "indicator_code"]).reset_index(
            drop=True
        )
        path = settings.processed_dir / f"{dataset_id}.parquet"
        temporary = Path(str(path) + ".tmp")
        frame.to_parquet(temporary, index=False, compression="zstd")
        temporary.replace(path)
        result[dataset_id] = _metadata(frame, dataset_id, filename)
    manifest_path = settings.processed_dir / "manifest.json"
    temp_manifest = manifest_path.with_suffix(".json.tmp")
    temp_manifest.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temp_manifest.replace(manifest_path)
    return result
