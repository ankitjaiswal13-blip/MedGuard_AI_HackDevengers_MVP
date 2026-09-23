import { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

// Relative API path — Vite proxy forwards /api/* to FastAPI during dev.
const API = import.meta.env.VITE_API_URL ?? "";

function App() {
  const [summary, setSummary] = useState(null);
  const [items, setItems] = useState([]);
  const [beds, setBeds] = useState([]);
  const [staff, setStaff] = useState([]);
  const [redistribution, setRedistribution] = useState([]);
  const [facilities, setFacilities] = useState([]);
  const [selectedFacility, setSelectedFacility] = useState("");
  const [forecast, setForecast] = useState(null);
  const [forecastMedicine, setForecastMedicine] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = async (facilityId = selectedFacility) => {
    setLoading(true);
    try {
      const q = facilityId ? `?facility_id=${encodeURIComponent(facilityId)}` : "";
      const [sRes, iRes, fRes, bRes, stRes, rRes] = await Promise.all([
        fetch(`${API}/api/summary${q}`),
        fetch(`${API}/api/inventory${q}`),
        fetch(`${API}/api/facilities`),
        fetch(`${API}/api/beds`),
        fetch(`${API}/api/staff`),
        fetch(`${API}/api/redistribution`),
      ]);
      if (!sRes.ok || !iRes.ok || !fRes.ok || !bRes.ok || !stRes.ok || !rRes.ok) {
        throw new Error(`Backend error: ${sRes.status} / ${iRes.status}`);
      }
      const [s, i, f, b, st, r] = await Promise.all([
        sRes.json(), iRes.json(), fRes.json(),
        bRes.json(), stRes.json(), rRes.json(),
      ]);
      setSummary(s);
      setItems(i);
      setFacilities(f);
      setBeds(b);
      setStaff(st);
      setRedistribution(r);
      setError(null);
    } catch (e) {
      console.error("Failed to load:", e);
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load("");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const onFacilityChange = (e) => {
    const value = e.target.value;
    setSelectedFacility(value);
    setForecast(null);
    load(value);
  };

  const showForecast = async (name, facilityId) => {
    setForecastMedicine({ name, facilityId });
    setForecast(null);
    try {
      const q = facilityId ? `&facility_id=${encodeURIComponent(facilityId)}` : "";
      const res = await fetch(
        `${API}/api/forecast/${encodeURIComponent(name)}?days=7${q}`
      );
      if (!res.ok) throw new Error(`Forecast failed (${res.status})`);
      const data = await res.json();
      if (data.error || data.detail) throw new Error(data.error || data.detail);
      setForecast(data);
    } catch (e) {
      console.error("Forecast failed:", e);
      setError(e.message);
      setForecastMedicine(null);
    }
  };

  const maxDemand = forecast
    ? Math.max(...forecast.predicted_daily_demand, 1)
    : 1;

  const statusClass = (s) => (s ? s.toLowerCase() : "low");

  return (
    <div className="app">
      <header>
        <div>
          <div className="brand">
            MedGuard <span>AI</span>
          </div>
          <div className="tag">Predict. Prevent. Protect.</div>
        </div>
        <div className="live">● LIVE INVENTORY</div>
      </header>

      <main>
        <section className="hero">
          <div>
            <h1>National Health Resource Intelligence</h1>
            <p>
              Real-time visibility into medicines, beds, and personnel across the
              PHC network — with demand forecasting and cross-district
              redistribution.
            </p>
          </div>
          <div className="facilitySelector">
            <label htmlFor="facility">View</label>
            <select
              id="facility"
              value={selectedFacility}
              onChange={onFacilityChange}
            >
              <option value="">All Facilities (National)</option>
              {facilities.map((f) => (
                <option key={f.facility_id} value={f.facility_id}>
                  {f.facility_name} — {f.district}
                </option>
              ))}
            </select>
          </div>
        </section>

        {error && (
          <section className="panel errorPanel">
            <strong>Something went wrong:</strong> {error}
            <button onClick={() => load(selectedFacility)}>Retry</button>
          </section>
        )}

        {loading && !summary && (
          <section className="panel loadingPanel">Loading dashboard…</section>
        )}

        {summary && (
          <section className="cards">
            <Card title="Medicines" value={summary.total_medicines} note="Tracked items" />
            <Card title="Critical" value={summary.critical} note="Immediate action" accent="critical" />
            <Card title="High Risk" value={summary.high} note="Needs attention" accent="high" />
            <Card title="Expiring ≤30d" value={summary.expiring_30_days} note="Prioritize stock" accent="medium" />
          </section>
        )}

        <section className="panel">
          <div className="panelHead">
            <h2>Inventory Risk Monitor</h2>
            <button onClick={() => load(selectedFacility)}>Refresh</button>
          </div>
          <div className="tableWrap">
            <table>
              <thead>
                <tr>
                  <th>Medicine</th>
                  {!selectedFacility && <th>Facility</th>}
                  <th>Stock</th>
                  <th>Daily Use</th>
                  <th>Days Left</th>
                  <th>Risk</th>
                  <th>Recommendation</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {items.map((x) => (
                  <tr key={`${x.facility_id}-${x.name}`}>
                    <td>
                      <b>{x.name}</b>
                      <small>{x.category}</small>
                    </td>
                    {!selectedFacility && (
                      <td>
                        <b>{x.facility_name}</b>
                        <small>{x.district}</small>
                      </td>
                    )}
                    <td>{x.quantity}</td>
                    <td>{x.daily_usage}</td>
                    <td>{x.days_of_stock}</td>
                    <td>
                      <span className={`risk ${x.risk.toLowerCase()}`}>{x.risk}</span>
                    </td>
                    <td>
                      {x.recommended_order > 0
                        ? `Order ${x.recommended_order} units`
                        : "No order needed"}
                    </td>
                    <td>
                      <button
                        className="forecastBtn"
                        onClick={() => showForecast(x.name, x.facility_id)}
                      >
                        Forecast
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {forecast && (
          <section className="panel forecast">
            <div className="panelHead">
              <h2>
                7-Day AI Forecast: {forecast.medicine}
                <small className="subTitle"> at {forecast.facility_name}</small>
              </h2>
              <button onClick={() => setForecast(null)}>Close</button>
            </div>
            <div className="forecastGrid">
              <div>
                <strong>{forecast.current_stock}</strong>
                <span>Current stock</span>
              </div>
              <div>
                <strong>{forecast.predicted_total_demand}</strong>
                <span>Predicted 7-day demand</span>
              </div>
              <div>
                <strong>{forecast.recommended_order}</strong>
                <span>Recommended order</span>
              </div>
            </div>
            <div className="bars">
              {forecast.predicted_daily_demand.map((v, i) => (
                <div className="barItem" key={i}>
                  <div
                    className="bar"
                    style={{ height: `${Math.max(8, (v / maxDemand) * 120)}px` }}
                  />
                  <small>D{i + 1}</small>
                </div>
              ))}
            </div>
          </section>
        )}

        <section className="twoCol">
          <div className="panel">
            <div className="panelHead">
              <h2>🛏️ Bed Availability</h2>
            </div>
            <div className="tableWrap">
              <table>
                <thead>
                  <tr>
                    <th>Facility</th>
                    <th>Total</th>
                    <th>Occupied</th>
                    <th>Available</th>
                    <th>Occupancy</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {beds.map((b) => (
                    <tr key={b.facility_id}>
                      <td>
                        <b>{b.facility_name}</b>
                        <small>{b.district}</small>
                      </td>
                      <td>{b.total_beds}</td>
                      <td>{b.occupied_beds}</td>
                      <td>{b.available_beds}</td>
                      <td>{b.occupancy_pct}%</td>
                      <td>
                        <span className={`risk ${statusClass(b.status)}`}>
                          {b.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="panel">
            <div className="panelHead">
              <h2>👩‍⚕️ Personnel Attendance</h2>
            </div>
            <div className="tableWrap">
              <table>
                <thead>
                  <tr>
                    <th>Facility</th>
                    <th>Role</th>
                    <th>Present</th>
                    <th>Total</th>
                    <th>Attendance</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {staff.map((s, i) => (
                    <tr key={`${s.facility_id}-${s.role}-${i}`}>
                      <td>
                        <b>{s.facility_name}</b>
                        <small>{s.district}</small>
                      </td>
                      <td>{s.role}</td>
                      <td>{s.present}</td>
                      <td>{s.total}</td>
                      <td>{s.attendance_pct}%</td>
                      <td>
                        <span className={`risk ${statusClass(s.status)}`}>
                          {s.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        <section className="panel redistributionPanel">
          <div className="panelHead">
            <h2>🔁 Cross-District Redistribution Recommendations</h2>
            <span className="liveBadge">
              {redistribution.length} active
            </span>
          </div>
          {redistribution.length === 0 ? (
            <p className="emptyMsg">
              No transfers needed — all facilities have adequate stock.
            </p>
          ) : (
            <div className="redistributionList">
              {redistribution.map((r, i) => {
                const highlighted =
                  selectedFacility && r.to_facility_id === selectedFacility;
                return (
                  <div
                    className={`redistributionCard${highlighted ? " highlighted" : ""}`}
                    key={i}
                  >
                    <div className="transferRoute">
                      <div className="transferSide">
                        <div className="transferLabel">FROM</div>
                        <div className="transferFacility">{r.from_facility}</div>
                        <div className="transferDistrict">{r.from_district}</div>
                      </div>
                      <div className="transferArrow">
                        <div className="transferMedicine">{r.medicine}</div>
                        <div className="arrow">→</div>
                        <div className="transferUnits">{r.transfer_units} units</div>
                      </div>
                      <div className="transferSide">
                        <div className="transferLabel">TO</div>
                        <div className="transferFacility">{r.to_facility}</div>
                        <div className="transferDistrict">{r.to_district}</div>
                      </div>
                    </div>
                    <div className="transferReason">{r.reason}</div>
                  </div>
                );
              })}
            </div>
          )}
        </section>
      </main>
      <footer>
        MedGuard AI · Nexovate · Hack Devengers 2.0 · Track 3 — Smart Health & Supply Chain Resilience
      </footer>
    </div>
  );
}

function Card({ title, value, note, accent }) {
  return (
    <div className={`card${accent ? ` accent-${accent}` : ""}`}>
      <span>{title}</span>
      <strong>{value}</strong>
      <small>{note}</small>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);