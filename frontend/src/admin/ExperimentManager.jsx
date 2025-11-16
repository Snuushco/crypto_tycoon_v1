import { useEffect, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:4000";

export default function ExperimentManager() {
  const [experiments, setExperiments] = useState([]);
  const [insights, setInsights] = useState([]);

  useEffect(() => {
    fetch(`${API_BASE}/api/experiments`)
      .then((res) => res.json())
      .then(setExperiments)
      .catch((err) => console.error(err));

    fetch(`${API_BASE}/api/analytics/insights`)
      .then((res) => res.json())
      .then((data) => setInsights(data?.suggestions ?? []))
      .catch((err) => console.error(err));
  }, []);

  return (
    <section className="card">
      <h2>Experiment Manager</h2>
      <div className="experiments">
        {experiments.map((experiment) => (
          <article key={experiment.id} className="experiment-card">
            <header>
              <h3>{experiment.id}</h3>
              <span className={experiment.active ? "pill active" : "pill"}>
                {experiment.active ? "Actief" : "Inactief"}
              </span>
            </header>
            <p>Assignment: {experiment.assignment}</p>
            <ul>
              {experiment.variants.map((variant) => (
                <li key={variant.id}>
                  <strong>{variant.id}</strong> — {JSON.stringify(variant)}
                </li>
              ))}
            </ul>
          </article>
        ))}
      </div>
      <h3>Automatische aanbevelingen</h3>
      <ul>
        {insights.length === 0 && <li>Nog geen aanbevelingen</li>}
        {insights.map((suggestion, idx) => (
          <li key={`${suggestion.type}-${idx}`}>
            <strong>{suggestion.type}:</strong> {suggestion.message}
          </li>
        ))}
      </ul>
    </section>
  );
}
