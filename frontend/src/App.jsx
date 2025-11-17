import AnalyticsDashboard from "./admin/AnalyticsDashboard";
import ExperimentManager from "./admin/ExperimentManager";
import CohortGraphs from "./admin/CohortGraphs";
import "./App.css";

function App() {
  const isAdmin = new URLSearchParams(window.location.search).get("admin") === "true";

  if (!isAdmin) {
    return (
      <main className="locked">
        <h1>Analytics Dashboard gelocked</h1>
        <p>
          Voeg <code>?admin=true</code> toe aan de URL om toegang te krijgen.
        </p>
      </main>
    );
  }

  return (
    <main className="admin-layout">
      <header>
        <h1>Crypto Tycoon v1 — Analytics & Experimentation</h1>
        <p>Live zicht op gedrag, monetization en lopende experimenten.</p>
      </header>
      <AnalyticsDashboard />
      <div className="columns">
        <ExperimentManager />
        <CohortGraphs />
      </div>
    </main>
  );
}

export default App;
