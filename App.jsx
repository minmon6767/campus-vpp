import { useEffect, useState, useCallback } from "react";
import { api } from "./api";
import StatCard from "./components/StatCard";
import ForecastChart from "./components/ForecastChart";
import RecommendationPanel from "./components/RecommendationPanel";

const REFRESH_MS = 30000;

export default function App() {
  const [current, setCurrent] = useState(null);
  const [history, setHistory] = useState([]);
  const [forecast, setForecast] = useState(null);
  const [recommendation, setRecommendation] = useState(null);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const loadAll = useCallback(async () => {
    try {
      const [currentRes, historyRes, forecastRes, recRes] = await Promise.all([
        api.current(),
        api.history(48),
        api.forecast(6),
        api.recommendation(),
      ]);
      setCurrent(currentRes);
      setHistory(historyRes.readings);
      setForecast(forecastRes);
      setRecommendation(recRes);
      setError(null);
      setLastUpdated(new Date());
    } catch (e) {
      setError(
        "Could not reach the Campus VPP API. Is the backend running at " +
          (import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000") +
          "? (See backend/README or the repo root README for setup.)"
      );
    }
  }, []);

  useEffect(() => {
    loadAll();
    const id = setInterval(loadAll, REFRESH_MS);
    return () => clearInterval(id);
  }, [loadAll]);

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <h1>Campus Virtual Power Plant</h1>
          <div className="subtitle">
            SVH26004 · Hybrid Renewable Energy Generation Solution — solar + wind + battery + grid, coordinated
          </div>
        </div>
        <span className="badge">PROTOTYPE · ~30% MATURITY</span>
      </header>

      {error && <div className="error-banner">{error}</div>}

      {current && (
        <div className="stat-grid">
          <StatCard label="Solar Generation" value={current.solar_kw.toFixed(0)} unit="kW" />
          <StatCard label="Wind Generation" value={current.wind_kw.toFixed(0)} unit="kW" />
          <StatCard label="Campus Demand" value={current.demand_kw.toFixed(0)} unit="kW" />
          <StatCard label="Battery SOC" value={current.battery_soc_pct.toFixed(0)} unit="%" />
          <StatCard label="Grid Import" value={current.grid_import_kw.toFixed(0)} unit="kW" />
        </div>
      )}

      <RecommendationPanel recommendation={recommendation} />

      <div className="panel">
        <h2>Generation, Demand &amp; 6-Hour Forecast</h2>
        {history.length > 0 && <ForecastChart history={history} forecast={forecast} />}
        <div className="status-line">
          Solid lines = actual telemetry (last 48h) · Dashed lines = forecast (next 6h)
          {lastUpdated && <> · Last updated {lastUpdated.toLocaleTimeString()}</>}
        </div>
      </div>

      <div className="footer-note">
        Synthetic demo data — standing in for live inverter/meter telemetry until hardware integration.
        See the project README for architecture details and how this maps to the SVH26004 proposal.
      </div>
    </div>
  );
}
