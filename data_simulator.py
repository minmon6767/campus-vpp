"""
data_simulator.py
------------------
Generates a synthetic but physically-plausible dataset of campus energy
telemetry: solar generation, wind generation, electrical demand, and
battery state-of-charge, at hourly resolution.

This stands in for the real sensor/meter feed described in the SVH26004
proposal (inverter + meter data ingested via Modbus/MQTT). It lets the
rest of the prototype (forecasting + optimisation + dashboard) run
end-to-end without needing live hardware.

The profile shapes are loosely based on typical Rajasthan solar/wind
patterns (strong, consistent daytime solar; intermittent wind, often
stronger in the evening/night) and a typical institutional campus load
(morning + evening peaks, low overnight baseline).
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta


SOLAR_CAPACITY_KW = 160.0
WIND_CAPACITY_KW = 60.0
BATTERY_CAPACITY_KWH = 200.0
BATTERY_MAX_RATE_KW = 50.0


@dataclass
class HourReading:
    timestamp: str
    solar_kw: float
    wind_kw: float
    demand_kw: float
    battery_soc_pct: float
    grid_import_kw: float


def _solar_profile(hour_of_day: float, cloud_factor: float) -> float:
    """Daytime bell curve, zero at night, peak around 13:00."""
    if hour_of_day < 6 or hour_of_day > 18:
        return 0.0
    x = (hour_of_day - 12) / 6.0
    base = math.exp(-3.2 * x * x)  # bell curve, ~0 at edges, 1 at noon
    return max(0.0, SOLAR_CAPACITY_KW * base * cloud_factor)


def _wind_profile(hour_of_day: float, rng: random.Random) -> float:
    """Noisy wind curve — generally light by day, gustier at night."""
    night_boost = 1.6 if (hour_of_day < 6 or hour_of_day > 19) else 1.0
    base = WIND_CAPACITY_KW * 0.28 * night_boost
    noise = rng.uniform(0.4, 1.3)
    return max(0.0, min(WIND_CAPACITY_KW, base * noise))


def _demand_profile(hour_of_day: float, rng: random.Random) -> float:
    """Campus load: morning ramp, midday plateau, evening peak, low overnight.

    Calibrated relative to SOLAR_CAPACITY_KW/WIND_CAPACITY_KW so that the
    demo shows the full range of dispatch behaviour: a genuine midday
    surplus (solar comfortably exceeds the plateau load, so CHARGE/EXPORT
    triggers), and a genuine evening deficit once the sun is down and load
    peaks (so DISCHARGE/HOLD triggers) — mirroring the real mismatch this
    project targets, rather than a campus that is simply undersized either way.
    """
    if 7 <= hour_of_day < 9:
        base = 55 + (hour_of_day - 7) * 15
    elif 9 <= hour_of_day < 17:
        base = 85
    elif 17 <= hour_of_day < 21:
        base = 125
    elif 21 <= hour_of_day < 23:
        base = 80
    else:
        base = 38
    return max(20.0, base * rng.uniform(0.92, 1.08))


def generate_series(start: datetime, hours: int, seed: int = 7) -> list[HourReading]:
    """Generate `hours` of synthetic hourly readings starting at `start`.

    Battery SOC is simulated forward using a simple greedy rule (charge on
    surplus, discharge on deficit) purely to produce a plausible historical
    trace — the *live* dispatch decision for new data is made by
    optimizer.recommend_action(), not by this function.
    """
    rng = random.Random(seed)
    readings: list[HourReading] = []
    soc_kwh = BATTERY_CAPACITY_KWH * 0.5

    # Multi-day cloud pattern so forecasting has some texture to learn from.
    cloud_by_day = {}

    for i in range(hours):
        ts = start + timedelta(hours=i)
        hour_of_day = ts.hour + ts.minute / 60.0
        day_key = ts.date()
        if day_key not in cloud_by_day:
            cloud_by_day[day_key] = rng.choice([0.95, 0.95, 0.85, 0.6, 0.9])
        cloud_factor = cloud_by_day[day_key]

        solar = _solar_profile(hour_of_day, cloud_factor)
        wind = _wind_profile(hour_of_day, rng)
        demand = _demand_profile(hour_of_day, rng)

        net = solar + wind - demand  # positive => surplus, negative => deficit
        if net > 0:
            charge = min(net, BATTERY_MAX_RATE_KW, (BATTERY_CAPACITY_KWH - soc_kwh))
            soc_kwh += charge
            grid_import = 0.0
        else:
            deficit = -net
            discharge = min(deficit, BATTERY_MAX_RATE_KW, soc_kwh)
            soc_kwh -= discharge
            grid_import = max(0.0, deficit - discharge)

        readings.append(
            HourReading(
                timestamp=ts.isoformat(),
                solar_kw=round(solar, 2),
                wind_kw=round(wind, 2),
                demand_kw=round(demand, 2),
                battery_soc_pct=round(100 * soc_kwh / BATTERY_CAPACITY_KWH, 1),
                grid_import_kw=round(grid_import, 2),
            )
        )

    return readings


def generate_history_csv(path: str, days: int = 14) -> None:
    """Write `days` of synthetic history to a CSV file (used to seed the demo)."""
    import csv

    start = datetime.now().replace(minute=0, second=0, microsecond=0) - timedelta(days=days)
    rows = generate_series(start, hours=days * 24)

    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(rows[0]).keys()))
        writer.writeheader()
        for r in rows:
            writer.writerow(asdict(r))


if __name__ == "__main__":
    generate_history_csv("data/historical_sample.csv", days=14)
    print("Wrote data/historical_sample.csv")
