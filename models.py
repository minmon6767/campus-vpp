"""Pydantic schemas for API responses."""

from __future__ import annotations

from pydantic import BaseModel


class CurrentReading(BaseModel):
    timestamp: str
    solar_kw: float
    wind_kw: float
    demand_kw: float
    battery_soc_pct: float
    grid_import_kw: float


class ForecastResponse(BaseModel):
    timestamps: list[str]
    solar_kw: list[float]
    wind_kw: list[float]
    demand_kw: list[float]


class RecommendationResponse(BaseModel):
    action: str
    magnitude_kw: float
    reason: str
    confidence: str


class HistoryResponse(BaseModel):
    readings: list[CurrentReading]
