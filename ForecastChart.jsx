import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
} from "recharts";

function formatHour(iso) {
  const d = new Date(iso);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export default function ForecastChart({ history, forecast }) {
  const historyRows = history.map((r) => ({
    time: formatHour(r.timestamp),
    solar: r.solar_kw,
    wind: r.wind_kw,
    demand: r.demand_kw,
    kind: "history",
  }));

  const forecastRows = forecast
    ? forecast.timestamps.map((ts, i) => ({
        time: formatHour(ts),
        solarForecast: forecast.solar_kw[i],
        windForecast: forecast.wind_kw[i],
        demandForecast: forecast.demand_kw[i],
        kind: "forecast",
      }))
    : [];

  const data = [...historyRows, ...forecastRows];
  const splitIndex = historyRows.length - 1;

  return (
    <ResponsiveContainer width="100%" height={320}>
      <ComposedChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e3ecee" />
        <XAxis dataKey="time" tick={{ fontSize: 11 }} interval="preserveStartEnd" />
        <YAxis tick={{ fontSize: 11 }} label={{ value: "kW", angle: -90, position: "insideLeft", fontSize: 11 }} />
        <Tooltip />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        {splitIndex >= 0 && (
          <ReferenceLine x={data[splitIndex]?.time} stroke="#f4a300" strokeDasharray="4 4" label={{ value: "now", fontSize: 10, fill: "#f4a300" }} />
        )}
        <Line type="monotone" dataKey="solar" name="Solar (actual)" stroke="#f4a300" dot={false} strokeWidth={2} connectNulls />
        <Line type="monotone" dataKey="wind" name="Wind (actual)" stroke="#0070c0" dot={false} strokeWidth={2} connectNulls />
        <Line type="monotone" dataKey="demand" name="Demand (actual)" stroke="#c0504d" dot={false} strokeWidth={2} connectNulls />
        <Line type="monotone" dataKey="solarForecast" name="Solar (forecast)" stroke="#f4a300" strokeDasharray="5 4" dot={false} strokeWidth={2} connectNulls />
        <Line type="monotone" dataKey="windForecast" name="Wind (forecast)" stroke="#0070c0" strokeDasharray="5 4" dot={false} strokeWidth={2} connectNulls />
        <Line type="monotone" dataKey="demandForecast" name="Demand (forecast)" stroke="#c0504d" strokeDasharray="5 4" dot={false} strokeWidth={2} connectNulls />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
