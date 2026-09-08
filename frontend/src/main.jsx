import React, {useEffect, useState} from "react";
import {createRoot} from "react-dom/client";
import "./styles.css";

const API = "http://localhost:8000";

function App(){
  const [summary,setSummary]=useState(null);
  const [items,setItems]=useState([]);
  const [selected,setSelected]=useState(null);
  const [forecast,setForecast]=useState(null);

  const load=async()=>{
    const [s,i]=await Promise.all([
      fetch(`${API}/api/summary`).then(r=>r.json()),
      fetch(`${API}/api/inventory`).then(r=>r.json())
    ]);
    setSummary(s); setItems(i);
  };

  useEffect(()=>{load()},[]);

  const showForecast = async (name) => {  
      setSelected(name);
    const response = await fetch(`${API}/api/forecast/${encodeURIComponent(name)}?days=7`);
    const data = await response.json();
    setForecast(data);
 };

  return <div className="app">
    <header>
      <div>
        <div className="brand">MedGuard <span>AI</span></div>
        <div className="tag">Predict. Prevent. Protect.</div>
      </div>
      <div className="live">● LIVE INVENTORY</div>
    </header>

    <main>
      <section className="hero">
        <h1>Medicine Inventory Intelligence</h1>
        <p>Predict demand, detect stock-out risk and reduce expiry losses.</p>
      </section>

      {summary && <section className="cards">
        <Card title="Medicines" value={summary.total_medicines} note="Tracked items"/>
        <Card title="Critical" value={summary.critical} note="Immediate action"/>
        <Card title="High Risk" value={summary.high} note="Needs attention"/>
        <Card title="Expiring ≤30d" value={summary.expiring_30_days} note="Prioritize stock"/>
      </section>}

      <section className="panel">
        <div className="panelHead">
          <h2>Inventory Risk Monitor</h2>
          <button onClick={load}>Refresh</button>
        </div>
        <div className="tableWrap">
          <table>
            <thead><tr><th>Medicine</th><th>Stock</th><th>Daily Use</th><th>Days Left</th><th>Risk</th><th>Recommendation</th><th></th></tr></thead>
            <tbody>{items.map(x=><tr key={x.name}>
              <td><b>{x.name}</b><small>{x.category}</small></td>
              <td>{x.quantity}</td>
              <td>{x.daily_usage}</td>
              <td>{x.days_of_stock}</td>
              <td><span className={`risk ${x.risk.toLowerCase()}`}>{x.risk}</span></td>
              <td>{x.recommended_order>0 ? `Order ${x.recommended_order} units` : "No order needed"}</td>
              <td><button className="forecastBtn" onClick={()=>showForecast(x.name)}>Forecast</button></td>
            </tr>)}</tbody>
          </table>
        </div>
      </section>

      {forecast && <section className="panel forecast">
        <div className="panelHead"><h2>7-Day AI Forecast: {selected}</h2><button onClick={()=>setForecast(null)}>Close</button></div>
        <div className="forecastGrid">
          <div><strong>{forecast.current_stock}</strong><span>Current stock</span></div>
          <div><strong>{forecast.predicted_total_demand}</strong><span>Predicted 7-day demand</span></div>
          <div><strong>{forecast.recommended_order}</strong><span>Recommended order</span></div>
        </div>
        <div className="bars">{forecast.predicted_daily_demand.map((v,i)=>
          <div className="barItem" key={i}><div className="bar" style={{height:`${Math.max(8,v*5)}px`}}></div><small>D{i+1}</small></div>
        )}</div>
      </section>}
    </main>
    <footer>MedGuard AI • Hack Devengers 2.0 • Hackathon MVP</footer>
  </div>
}

function Card({title,value,note}) {
  return <div className="card"><span>{title}</span><strong>{value}</strong><small>{note}</small></div>
}

createRoot(document.getElementById("root")).render(<App/>);
