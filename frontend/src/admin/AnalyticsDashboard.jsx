import { useEffect, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:4000";

export default function AnalyticsDashboard() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function load() {
      try {
        const response = await fetch(`${API_BASE}/api/analytics/summary`);
        if (!response.ok) throw new Error("Kon metrics niet ophalen");
        const data = await response.json();
        setMetrics(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) return <section>Metrics laden...</section>;
  if (error) return <section className="error">{error}</section>;
  if (!metrics) return null;

  return (
    <section className="card">
      <h2>Kernmetrics</h2>
      <div className="grid">
        <Metric label="DAU" value={metrics.dau} />
        <Metric label="WAU" value={metrics.wau} />
        <Metric label="MAU" value={metrics.mau} />
        <Metric label="Sessieduur" value={`${metrics.sessionLengthAvg}s`} />
        <Metric label="D1 Retention" value={metrics.retention.d1} />
        <Metric label="D3 Retention" value={metrics.retention.d3} />
        <Metric label="D7 Retention" value={metrics.retention.d7} />
        <Metric label="Purchase CVR" value={metrics.purchaseConversionRate} />
        <Metric label="Prestige Frequency" value={metrics.prestigeFrequency} />
        <Metric label="Booster Usage" value={metrics.boosterUsage} />
      </div>
      <div className="card">
        <h3>Purchase Breakdown</h3>
        <ul>
          {Object.entries(metrics.purchaseBreakdown).map(([product, count]) => (
            <li key={product}>
              <strong>{product}</strong>: {count}
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

function Metric({ label, value }) {
  return (
    <div className="metric">
      <p className="metric-label">{label}</p>
      <p className="metric-value">{value ?? 0}</p>
    </div>
  );
}
