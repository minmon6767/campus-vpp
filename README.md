# Campus VPP — Hybrid Renewable Energy Generation Solution

**SVH26004** · Smart VIT Hackathon 2026 · Government of Rajasthan, Directorate of Technical Education · Category: Software

A software orchestration layer that treats a campus's solar panels, wind turbine, battery storage, and grid connection as one coordinated **virtual power plant (VPP)** — instead of letting them run as independent, unmanaged assets.

This repo is the working prototype behind the idea: a real backend (data simulation, short-term forecasting, and a rule-based dispatch optimiser) exposed through a REST API, and a live dashboard that consumes it.

![Dashboard screenshot](docs/dashboard_screenshot.png)

## Why this exists

Public-sector campuses across Rajasthan already have solar and (sometimes) wind installed, but:

- Assets run in isolation — no coordinated scheduling between solar, wind, and battery
- Peak solar output often exceeds demand and is wasted, while calm/cloudy periods force a full revert to grid power
- Batteries, where present, cycle on fixed rules rather than real-time forecasts
- Facilities staff have no predictive view — only fragmented, manually-checked meter readings

See the full pitch deck and problem-statement mapping in [`docs/`](docs/).

## How it works

```
Sensors & Meters → Data Ingestion → Forecast Engine → Optimisation Engine → Dashboard & Auto-Actions
```

1. **Data layer** (`backend/app/data_simulator.py`) — stands in for live inverter/meter telemetry (Modbus/MQTT in production) with a physically-plausible synthetic dataset: a daytime solar bell curve, noisy wind, a realistic campus demand profile (morning ramp, midday plateau, evening peak), and a simulated battery state-of-charge.
2. **Forecast engine** (`backend/app/forecasting.py`) — predicts the next 1–12 hours of solar, wind, and demand using a seasonal-naive + short-trend blend. This is the lightweight, dependency-free stand-in for the LSTM/Prophet models named as the production target in the proposal — same interface, swappable later.
3. **Optimisation engine** (`backend/app/optimizer.py`) — a rule-based dispatch decision (CHARGE / DISCHARGE / EXPORT / HOLD) with a plain-language reason and a confidence score, based on current state + forecast agreement. Stands in for the MILP-based optimiser named as the production target.
4. **API** (`backend/app/main.py`) — FastAPI service exposing all of the above.
5. **Dashboard** (`frontend/`) — a React + Recharts UI: live stat cards, the current dispatch recommendation, and a combined actual-vs-forecast chart.

This mirrors exactly the architecture diagram on the Technical Approach slide of the submission deck — nothing in the dashboard is hard-coded; every number comes from the API.

## Project status

**~30% prototype maturity**, as stated in the submission: the forecasting model and dashboard are built and validated against historical (synthetic) data; live sensor/inverter integration is the next milestone. The rule-based optimiser and seasonal-naive forecaster are intentionally simple, dependency-light implementations that prove out the *architecture and interfaces* end-to-end — they're designed to be swapped for the MILP optimiser and LSTM/Prophet forecaster named in the proposal without changing the API contract or the frontend.

## Quickstart

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate   # optional but recommended
pip install -r requirements.txt
python3 app/data_simulator.py                         # generates data/historical_sample.csv
uvicorn app.main:app --reload --port 8000
```

The API is now live at `http://127.0.0.1:8000`. Interactive docs at `http://127.0.0.1:8000/docs`.

Run the test suite:

```bash
pytest tests/ -v
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`. It talks to the backend at `http://127.0.0.1:8000` by default — override with a `.env` file (see `frontend/.env.example`) if your backend runs elsewhere.

## API reference

| Endpoint | Description |
|---|---|
| `GET /api/health` | Liveness check |
| `GET /api/current` | Most recent reading (solar/wind/demand/battery SOC/grid import) |
| `GET /api/history?hours=48` | Historical telemetry for charting |
| `GET /api/forecast?horizon=6` | Next N hours of solar/wind/demand forecast |
| `GET /api/recommendation` | Current dispatch recommendation with reasoning |

Full interactive schema at `/docs` once the backend is running (FastAPI's built-in Swagger UI).

## Repository layout

```
campus-vpp/
├── backend/
│   ├── app/
│   │   ├── main.py            FastAPI app & routes
│   │   ├── data_simulator.py  Synthetic telemetry generator
│   │   ├── forecasting.py     Seasonal-naive + trend forecaster
│   │   ├── optimizer.py       Rule-based dispatch engine
│   │   └── models.py          Pydantic response schemas
│   ├── tests/                 pytest suite (16 tests)
│   ├── data/historical_sample.csv
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api.js
│   │   └── components/        StatCard, ForecastChart, RecommendationPanel
│   └── package.json
├── docs/                      Architecture notes, screenshot
└── .github/workflows/ci.yml   Lint + test on push
```

## License

MIT — see [LICENSE](LICENSE).
