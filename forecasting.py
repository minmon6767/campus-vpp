"""
forecasting.py
--------------
Short-term (next 1-12h) forecasting of solar generation, wind generation,
and campus demand.

Method: seasonal-naive blended with a short local trend.
    forecast(h) = same_hour_yesterday(h) * (1 - w) + recent_trend_projection(h) * w

This is intentionally a lightweight, dependency-light statistical method
(no model training/GPU needed) rather than the LSTM/Prophet models named
in the pitch deck as the target production approach. It is a faithful
stand-in for this prototype stage (~30% maturity): it demonstrates the
*interface* the optimisation engine consumes (an hourly forecast for
solar/wind/demand) so the rest of the system — the recommendation logic
and the dashboard — can be built and demoed against something real,
while the production model is swapped in later without changing any
downstream code.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Sequence

from .data_simulator import HourReading


def _series(readings: Sequence[HourReading], field: str) -> list[float]:
    return [getattr(r, field) for r in readings]


def _seasonal_naive_trend_forecast(history: list[float], horizon: int, day_len: int = 24) -> list[float]:
    """Blend "same hour, previous day" with a short linear trend of the last few points."""
    n = len(history)
    forecast: list[float] = []

    # Short local trend from the last 3 observed points (simple linear fit).
    tail = history[-3:] if n >= 3 else history[-1:]
    if len(tail) >= 2:
        slope = (tail[-1] - tail[0]) / (len(tail) - 1)
    else:
        slope = 0.0

    for h in range(1, horizon + 1):
        idx_yesterday = n - day_len + (h - 1)
        seasonal = history[idx_yesterday] if 0 <= idx_yesterday < n else history[-1]
        trend_proj = history[-1] + slope * h
        # Trend weight decays with horizon distance — trust recent trend more
        # in the next couple of hours, seasonal pattern more further out.
        w_trend = max(0.15, 0.55 - 0.05 * h)
        value = seasonal * (1 - w_trend) + trend_proj * w_trend
        forecast.append(max(0.0, round(value, 2)))

    return forecast


def forecast_next_hours(history: list[HourReading], horizon: int = 6) -> dict:
    """Return solar/wind/demand forecasts for the next `horizon` hours.

    Requires at least ~24h of history for the seasonal component to be
    meaningful; falls back gracefully (flat persistence) if less is given.
    """
    if len(history) < 6:
        raise ValueError("Need at least 6 hours of history to forecast")

    last_ts = datetime.fromisoformat(history[-1].timestamp)
    timestamps = [(last_ts + timedelta(hours=h)).isoformat() for h in range(1, horizon + 1)]

    solar_hist = _series(history, "solar_kw")
    wind_hist = _series(history, "wind_kw")
    demand_hist = _series(history, "demand_kw")

    return {
        "timestamps": timestamps,
        "solar_kw": _seasonal_naive_trend_forecast(solar_hist, horizon),
        "wind_kw": _seasonal_naive_trend_forecast(wind_hist, horizon),
        "demand_kw": _seasonal_naive_trend_forecast(demand_hist, horizon),
    }
