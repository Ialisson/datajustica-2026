from __future__ import annotations

from dataclasses import asdict
from datetime import date
from typing import Annotated, Literal

from fastapi import FastAPI, HTTPException, Query

from datajustica.sources.catalog import SOURCES
from datajustica.storage.warehouse import (
    DATASETS,
    get_observations,
    list_areas,
    list_indicators,
    metadata,
)

app = FastAPI(
    title="DataJustiça API",
    version="0.2.0",
    description=(
        "API local para explorar séries abertas do ISP-RJ, "
        "mantendo fonte e granularidade explícitas."
    ),
)
Dataset = Literal["municipality_counts", "municipality_rates", "cisp_femicide"]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/sources")
def sources() -> list[dict[str, str]]:
    return [{"source_id": key, **asdict(source)} for key, source in SOURCES.items()]


@app.get("/v1/datasets")
def datasets() -> dict[str, object]:
    return {"datasets": DATASETS, "metadata": metadata()}


@app.get("/v1/indicators")
def indicators(dataset: Dataset = "municipality_counts") -> list[dict[str, str]]:
    try:
        return list_indicators(dataset)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/v1/areas")
def areas(dataset: Dataset = "municipality_counts") -> list[str]:
    try:
        return list_areas(dataset)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/v1/observations")
def observations(
    dataset: Dataset = "municipality_counts",
    indicator: Annotated[list[str] | None, Query()] = None,
    area: Annotated[list[str] | None, Query()] = None,
    start: date | None = None,
    end: date | None = None,
    limit: int = Query(default=10_000, ge=1, le=100_000),
) -> dict[str, object]:
    if start and end and start > end:
        raise HTTPException(status_code=422, detail="start deve ser anterior ou igual a end")
    try:
        frame = get_observations(
            dataset, indicators=indicator, areas=area, start=start, end=end
        ).head(limit)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    frame["period_start"] = frame["period_start"].astype(str)
    return {"count": len(frame), "data": frame.to_dict(orient="records")}
