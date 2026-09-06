const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

async function getJSON(path) {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    throw new Error(`Request to ${path} failed with status ${res.status}`);
  }
  return res.json();
}

export const api = {
  current: () => getJSON("/api/current"),
  history: (hours = 48) => getJSON(`/api/history?hours=${hours}`),
  forecast: (horizon = 6) => getJSON(`/api/forecast?horizon=${horizon}`),
  recommendation: () => getJSON("/api/recommendation"),
};
