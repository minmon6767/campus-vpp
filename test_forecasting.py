from datetime import datetime, timedelta

from app.data_simulator import generate_series
from app.forecasting import forecast_next_hours


def test_generate_series_produces_expected_length_and_bounds():
    start = datetime(2026, 1, 1, 0, 0)
    readings = generate_series(start, hours=48)
    assert len(readings) == 48
    for r in readings:
        assert r.solar_kw >= 0
        assert r.wind_kw >= 0
        assert r.demand_kw > 0
        assert 0 <= r.battery_soc_pct <= 100


def test_solar_is_zero_overnight_and_positive_midday():
    start = datetime(2026, 1, 1, 0, 0)
    readings = generate_series(start, hours=24)
    midnight = readings[0]
    noon = readings[13]  # hour index 13 ~ 13:00
    assert midnight.solar_kw == 0.0
    assert noon.solar_kw > 0.0


def test_forecast_returns_requested_horizon():
    start = datetime(2026, 1, 1, 0, 0)
    readings = generate_series(start, hours=72)
    fc = forecast_next_hours(readings, horizon=6)
    assert len(fc["timestamps"]) == 6
    assert len(fc["solar_kw"]) == 6
    assert len(fc["wind_kw"]) == 6
    assert len(fc["demand_kw"]) == 6


def test_forecast_requires_minimum_history():
    start = datetime(2026, 1, 1, 0, 0)
    readings = generate_series(start, hours=3)
    try:
        forecast_next_hours(readings, horizon=6)
        assert False, "expected ValueError"
    except ValueError:
        pass
