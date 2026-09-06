"""
main.py
-------
FastAPI application exposing the Campus VPP prototype's API.

Endpoints
    GET /api/health           liveness check
    GET /api/history          recent historical telemetry (for charts)
    GET /api/current          most recent reading
    GET /api/forecast         next-N-hour forecast for solar/wind/demand
    GET /api/recommendation   current dispatch recommendation

On startup, if no historical data file is present, a fresh synthetic
dataset is generated so the demo runs standalone with zero setup.
"""

from __future__ import annotations

import csv
import os
from contextlib import asynccontextmanager
from dataclasses import asdict
from datetime import datetime, timedelta

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from .data_simulator import HourReading, generate_series
from .forecasting import forecast_next_hours
from .optimizer import recommend_action
from .models import (
    CurrentReading,
    ForecastResponse,
    RecommendationResponse,
    HistoryResponse,
)

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "historical_sample.csv")

_history: list[HourReading] = []


def _load_or_generate_history() -> list[HourReading]:
    if os.path.exists(DATA_PATH):
        readings = []
        with open(DATA_PATH, newline="") as f:
            for row in csv.DictReader(f):
                readings.append(
                    HourReading(
                        timestamp=row["timestamp"],
                        solar_kw=float(row["solar_kw"]),
                        wind_kw=float(row["wind_kw"]),
                        demand_kw=float(row["demand_kw"]),
                        battery_soc_pct=float(row["battery_soc_pct"]),
                        grid_import_kw=float(row["grid_import_kw"]),
                    )
                )
        if readings:
            return readings

    # Fallback: generate on the fly (keeps the demo runnable with zero setup)
    start = datetime.now().replace(minute=0, second=0, microsecond=0) - timedelta(days=14)
    return generate_series(start, hours=14 * 24)


@asynccontextmanager
async def lifespan(_: FastAPI):
    global _history
    _history = _load_or_generate_history()
    yield


app = FastAPI(
    title="Campus VPP API",
    description=(
        "Prototype API for the Hybrid Renewable Energy Generation Solution "
        "(SVH26004) — a software orchestration layer coordinating solar, "
        "wind, battery, and grid on a public-sector campus."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # demo-only; restrict in production
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "readings_loaded": len(_history)}


@app.get("/api/history", response_model=HistoryResponse)
def history(hours: int = Query(48, ge=1, le=24 * 14)) -> HistoryResponse:
    subset = _history[-hours:]
    return HistoryResponse(readings=[CurrentReading(**asdict(r)) for r in subset])


@app.get("/api/current", response_model=CurrentReading)
def current() -> CurrentReading:
    return CurrentReading(**asdict(_history[-1]))


@app.get("/api/forecast", response_model=ForecastResponse)
def forecast(horizon: int = Query(6, ge=1, le=12)) -> ForecastResponse:
    result = forecast_next_hours(_history, horizon=horizon)
    return ForecastResponse(**result)


@app.get("/api/recommendation", response_model=RecommendationResponse)
def recommendation() -> RecommendationResponse:
    latest = _history[-1]
    fc = forecast_next_hours(_history, horizon=1)
    forecast_net = fc["solar_kw"][0] + fc["wind_kw"][0] - fc["demand_kw"][0]

    rec = recommend_action(
        solar_kw=latest.solar_kw,
        wind_kw=latest.wind_kw,
        demand_kw=latest.demand_kw,
        battery_soc_pct=latest.battery_soc_pct,
        forecast_next_hour_net_kw=forecast_net,
    )
    return RecommendationResponse(**asdict(rec))
