import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";
const WS = import.meta.env.VITE_WS_URL || "ws://localhost:8000";

type Device = { id: string; name: string; created_at: string };
type Telemetry = { event_id: string; device_id: string; recorded_at: string; payload: Record<string, unknown> };

function App() {
  const [token, setToken] = useState(localStorage.getItem("token") || "");
  const [email, setEmail] = useState("demo@example.com");
  const [password, setPassword] = useState("password123");
  const [devices, setDevices] = useState<Device[]>([]);
  const [selected, setSelected] = useState("");
  const [rows, setRows] = useState<Telemetry[]>([]);
  const [live, setLive] = useState<Telemetry[]>([]);
  const [error, setError] = useState("");

  const headers = useMemo(() => ({ "Content-Type": "application/json", Authorization: `Bearer ${token}` }), [token]);

  async function auth(mode: "login" | "register") {
    setError("");
    const r = await fetch(`${API}/api/auth/${mode}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email, password }) });
    if (!r.ok) { setError(await r.text()); return; }
    const data = await r.json();
    localStorage.setItem("token", data.access_token);
    setToken(data.access_token);
  }

  async function refreshDevices() {
    if (!token) return;
    const r = await fetch(`${API}/api/devices`, { headers });
    if (r.ok) {
      const data = await r.json(); setDevices(data);
      if (!selected && data.length) setSelected(data[0].id);
    }
  }

  async function createDevice() {
    const name = prompt("Device name", `sensor-${devices.length + 1}`);
    if (!name) return;
    await fetch(`${API}/api/devices`, { method: "POST", headers, body: JSON.stringify({ name }) });
    await refreshDevices();
  }

  async function refreshHistory() {
    if (!selected) return;
    const r = await fetch(`${API}/api/devices/${selected}/telemetry?limit=50`, { headers });
    if (r.ok) setRows(await r.json());
  }

  async function sendSample() {
    if (!selected) return;
    await fetch(`${API}/api/devices/${selected}/telemetry`, {
      method: "POST", headers, body: JSON.stringify({ metrics: { temperature_c: +(20 + Math.random() * 8).toFixed(2), cpu_pct: +(10 + Math.random() * 70).toFixed(1) } })
    });
  }

  useEffect(() => { refreshDevices(); }, [token]);
  useEffect(() => { refreshHistory(); }, [selected]);
  useEffect(() => {
    if (!selected || !token) return;
    setLive([]);
    const ws = new WebSocket(`${WS}/ws/devices/${selected}?token=${encodeURIComponent(token)}`);
    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      const row: Telemetry = { event_id: msg.event_id, device_id: msg.device_id, recorded_at: msg.recorded_at, payload: msg.payload };
      setLive(prev => [row, ...prev].slice(0, 20));
      setRows(prev => [row, ...prev].slice(0, 50));
    };
    const ping = window.setInterval(() => ws.readyState === WebSocket.OPEN && ws.send("ping"), 15000);
    return () => { clearInterval(ping); ws.close(); };
  }, [selected, token]);

  if (!token) return <main className="auth"><section className="card"><h1>Device Platform</h1><p>Sign in to manage devices and watch telemetry.</p><input value={email} onChange={e=>setEmail(e.target.value)} placeholder="Email"/><input type="password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="Password"/><div className="row"><button onClick={()=>auth("login")}>Login</button><button className="secondary" onClick={()=>auth("register")}>Register</button></div>{error && <pre className="error">{error}</pre>}</section></main>;

  return <main><header><div><h1>Real-Time Device Management</h1><span>{email}</span></div><button className="secondary" onClick={()=>{localStorage.removeItem("token"); setToken("");}}>Logout</button></header><div className="layout"><aside className="card"><div className="row space"><h2>Devices</h2><button onClick={createDevice}>+ Add</button></div>{devices.map(d=><button key={d.id} className={`device ${selected===d.id?"active":""}`} onClick={()=>setSelected(d.id)}>{d.name}<small>{d.id.slice(0,8)}</small></button>)}</aside><section className="stack"><div className="card"><div className="row space"><div><h2>Live telemetry</h2><p>Redis pub/sub → WebSocket</p></div><button onClick={sendSample} disabled={!selected}>Send sample</button></div>{live.length===0?<p className="muted">No live events yet.</p>:<EventTable rows={live.slice(0,5)}/>}</div><div className="card"><div className="row space"><div><h2>History</h2><p>PostgreSQL, newest first</p></div><button className="secondary" onClick={refreshHistory}>Refresh</button></div><EventTable rows={rows}/></div></section></div></main>;
}

function EventTable({ rows }: { rows: Telemetry[] }) {
  return <div className="tableWrap"><table><thead><tr><th>Time</th><th>Event</th><th>Payload</th></tr></thead><tbody>{rows.map(r=><tr key={r.event_id}><td>{new Date(r.recorded_at).toLocaleTimeString()}</td><td><code>{r.event_id.slice(0,8)}</code></td><td><code>{JSON.stringify(r.payload)}</code></td></tr>)}</tbody></table></div>;
}

createRoot(document.getElementById("root")!).render(<React.StrictMode><App /></React.StrictMode>);
