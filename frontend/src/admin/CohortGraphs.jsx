import { useEffect, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:4000";

export default function CohortGraphs() {
  const [metrics, setMetrics] = useState(null);

  useEffect(() => {
    fetch(`${API_BASE}/api/analytics/summary`)
      .then((res) => res.json())
      .then(setMetrics)
      .catch((err) => console.error(err));
  }, []);

  if (!metrics) return null;

  const retention = metrics.retention ?? { d1: 0, d3: 0, d7: 0 };

  return (
    <section className="card">
      <h2>Cohort Trends</h2>
      <div className="cohort-grid">
        {Object.entries(retention).map(([label, value]) => (
          <div key={label} className="cohort-bar">
            <div className="bar" style={{ height: `${value * 100}%` }} />
            <p>{label.toUpperCase()}</p>
            <span>{Math.round(value * 100)}%</span>
          </div>
        ))}
      </div>
    </section>
  );
}
