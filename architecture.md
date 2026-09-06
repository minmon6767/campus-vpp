# Architecture

```
┌──────────────┐   ┌───────────────┐   ┌───────────────────┐   ┌────────────────────┐   ┌──────────────────────┐
│ Sensors &    │──▶│ Data Ingestion│──▶│ Forecast Engine    │──▶│ Optimisation Engine│──▶│ Dashboard &           │
│ Meters       │   │               │   │ (Weather + ML)     │   │ (Dispatch decision)│   │ Auto-Actions          │
└──────────────┘   └───────────────┘   └───────────────────┘   └────────────────────┘   └──────────────────────┘
```

This is the same five-stage pipeline shown on the Technical Approach slide of the submission deck. In this prototype:

| Stage | Production target (per proposal) | This prototype |
|---|---|---|
| Sensors & Meters | Modbus/SunSpec, MQTT adapters on real inverters/batteries | `data_simulator.py` — synthetic but physically-plausible telemetry |
| Data Ingestion | FastAPI microservices, TimescaleDB | FastAPI + in-memory/CSV (swap-in ready) |
| Forecast Engine | LSTM/Prophet trained on historical + weather data | Seasonal-naive + short-trend blend (`forecasting.py`) |
| Optimisation Engine | MILP-based dispatch solver | Rule-based decision tree (`optimizer.py`) |
| Dashboard | React + Recharts | React + Recharts (same — this part is production-shaped already) |

## Why simplified forecast/optimiser at this stage

The goal of this prototype is to prove the **end-to-end architecture and API contract** work — that data flows cleanly from ingestion through forecasting and optimisation to a dashboard a non-specialist can act on. The forecasting and optimisation *interfaces* (`forecast_next_hours()` returning per-hour solar/wind/demand arrays; `recommend_action()` returning an action + reason + confidence) are exactly what a production LSTM model or MILP solver would need to satisfy. Swapping either implementation later requires no changes to the API layer, the tests, or the frontend.

## Dispatch decision logic

`optimizer.recommend_action()` follows this decision order:

1. **Surplus** (generation − demand > threshold): charge the battery if it has headroom, otherwise export to the grid.
2. **Deficit** (demand − generation > threshold): discharge the battery if it has charge available, otherwise hold and accept grid import (flagging that non-critical load could be shifted).
3. **Roughly balanced**: opportunistically top up the battery if it's low and there's any small surplus; otherwise hold.

Each recommendation also reports a confidence level (HIGH/MEDIUM/LOW) based on whether the next-hour forecast agrees with the current trend — giving facilities staff a signal for how much to trust an "export now" vs. "wait and see" call.

## Data flow

1. On backend startup, `main.py` loads `data/historical_sample.csv` (or generates a fresh 14-day synthetic history if the file is missing) into memory.
2. `GET /api/current` returns the latest reading.
3. `GET /api/forecast` calls `forecasting.forecast_next_hours()` against the in-memory history.
4. `GET /api/recommendation` combines the latest reading with a 1-hour forecast and calls `optimizer.recommend_action()`.
5. The frontend polls all four endpoints every 30 seconds and re-renders the chart, stat cards, and recommendation panel.
