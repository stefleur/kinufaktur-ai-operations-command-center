import { useCallback, useEffect, useState } from "react";
import { request } from "../api/tasksApi";

function Badge({ value }) {
  return <span className={`state-badge ${["healthy", "resolved", "completed", "OK"].includes(value) ? "good" : "attention"}`}>{value || "unknown"}</span>;
}
function time(value) { return value ? new Date(typeof value === "number" ? value * 1000 : value).toLocaleString() : "—"; }

export default function OperationsDashboard() {
  const [overview, setOverview] = useState(null);
  const [telemetry, setTelemetry] = useState({ traces: [], logs: [] });
  const [selected, setSelected] = useState(null);
  const [traceFilter, setTraceFilter] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [demoMessage, setDemoMessage] = useState("");
  const refresh = useCallback(async () => {
    try {
      const [next, signals] = await Promise.all([request("/ops/overview"), request("/ops/telemetry")]);
      setOverview(next); setTelemetry(signals); setError("");
      setSelected((previous) => previous ? next.incidents.find((item) => item.id === previous.id) || previous : null);
      return next;
    } catch (failure) { setError(failure.message); return null; }
  }, []);
  useEffect(() => {
    refresh();
    const timer = window.setInterval(refresh, 5000);
    return () => window.clearInterval(timer);
  }, [refresh]);

  async function runWorkflow() {
    setBusy(true); setDemoMessage("");
    try {
      await request("/workflows/run", { method: "POST" });
      setDemoMessage("Workflow completed successfully.");
    } catch (failure) { setDemoMessage(`Workflow failed: ${failure.message} The on-call agent's recorded outcome appears below.`); }
    await refresh(); setBusy(false);
  }
  async function injectFault() {
    setBusy(true); setDemoMessage("");
    try {
      await request("/ops/demo/fault", { method: "POST" });
      setDemoMessage("The isolated demo dependency is faulted. Run a workflow to produce a real failure and activate on-call response.");
    } catch (failure) { setDemoMessage(failure.message); }
    await refresh(); setBusy(false);
  }
  const metrics = overview?.metrics || {};
  const incidents = overview?.incidents || [];
  const alerts = overview?.alerts || [];
  const traces = telemetry.traces.filter((item) => !traceFilter || item.trace_id.includes(traceFilter));
  const logs = telemetry.logs.filter((item) => !traceFilter || item.trace_id?.includes(traceFilter));

  return <main className="operations-dashboard">
    <section className="ops-intro">
      <div><div className="eyebrow">LIVE OPERATIONS · REFRESHES EVERY 5 SECONDS</div><h2>Keep work moving.</h2><p>Business workflows, service signals, and incident response in one place.</p></div>
      <button className="secondary-button" onClick={refresh}>Refresh signals</button>
    </section>
    {error && <p role="alert" className="ops-error">Operations signals unavailable: {error}</p>}
    {!overview && !error && <p role="status">Loading operations signals…</p>}
    <section className="metric-grid" aria-label="Operational metrics">
      <div className="metric-card"><span>Service health</span><strong><Badge value={overview?.health.status} /></strong><small>Live dependency health check</small></div>
      <div className="metric-card"><span>Requests observed</span><strong>{metrics.request_count ?? "—"}</strong><small>{metrics.error_count ?? 0} failed requests</small></div>
      <div className="metric-card"><span>Error rate</span><strong>{metrics.error_rate === undefined ? "—" : `${(metrics.error_rate * 100).toFixed(1)}%`}</strong><small>Persisted request history</small></div>
      <div className="metric-card"><span>Average latency</span><strong>{metrics.average_latency_ms === undefined ? "—" : `${Number(metrics.average_latency_ms).toFixed(1)} ms`}</strong><small>Backend request duration</small></div>
    </section>
    <div className="ops-columns">
      <section className="ops-panel workflow-panel"><div className="panel-heading"><h3>Workflow control</h3><Badge value={overview?.health.dependency?.status} /></div><p>Run a synthetic business workflow through the isolated dependency. Failures generate a correlated alert and automatically activate the bounded on-call agent.</p><div className="workflow-stats"><span><b>{metrics.workflow_count ?? 0}</b> workflows</span><span><b>{metrics.failed_workflow_count ?? 0}</b> failed workflows</span></div><div className="workflow-actions"><button className="primary-button" disabled={busy} onClick={runWorkflow}>{busy ? "Working…" : "Run workflow"}</button><button className="secondary-button" disabled={busy} onClick={injectFault}>Inject demo fault</button></div><small>Fault injection requires DEMO_MODE. Only the synthetic dependency can be remediated.</small>{demoMessage && <p role="status" className="demo-message">{demoMessage}</p>}</section>
      <section className="ops-panel"><div className="panel-heading"><h3>Impact alerts</h3><span className="count-label">{alerts.filter((alert) => alert.state === "firing").length} firing</span></div>{alerts.length === 0 ? <p className="panel-empty">No alerts recorded. A failed workflow triggers the user-impact rule.</p> : <ul className="signal-list">{alerts.slice(0, 6).map((alert) => <li key={alert.id}><div><strong>{alert.rule.replaceAll("_", " ")}</strong><small>{time(alert.timestamp)} · threshold {alert.threshold}</small></div><Badge value={alert.state} /></li>)}</ul>}</section>
    </div>
    <section className="ops-panel"><div className="panel-heading"><div><div className="eyebrow">AUTONOMOUS RESPONSE</div><h3>Incident history</h3></div><span className="count-label">{incidents.length} recorded</span></div>{incidents.length === 0 ? <p className="panel-empty">No incidents yet. Run the failure demonstration above to inspect the complete response timeline.</p> : <div className="incident-layout"><ul className="incident-list">{incidents.map((incident) => <li key={incident.id}><button className={selected?.id === incident.id ? "selected" : ""} onClick={() => { setSelected(incident); setTraceFilter(incident.trace_id); }}><div><strong>{incident.diagnosis || "Workflow failure"}</strong><small>{time(incident.timestamp)}</small></div><Badge value={incident.status} /></button></li>)}</ul><article className="incident-detail">{selected ? <><div className="panel-heading"><h4>Incident timeline</h4><Badge value={selected.status} /></div><p>{selected.diagnosis}</p><p><b>Action:</b> {selected.action || "None recorded"}</p><p><b>Result:</b> {typeof selected.result === "object" ? JSON.stringify(selected.result) : selected.result}</p><button className="trace-link" onClick={() => setTraceFilter(selected.trace_id)}>Trace {selected.trace_id}</button><ol className="timeline">{selected.timeline.map((entry, index) => <li key={index}><strong>{entry.event}</strong><small>{time(entry.timestamp)}</small>{entry.tool && <code>{entry.tool}</code>}{entry.result && <p>{typeof entry.result === "object" ? JSON.stringify(entry.result) : String(entry.result)}</p>}</li>)}</ol></> : <p className="panel-empty">Select an incident to view diagnosis, tool calls, and recovery evidence.</p>}</article></div>}</section>
    <section className="ops-panel telemetry-panel"><div className="panel-heading"><div><div className="eyebrow">CORRELATED TELEMETRY</div><h3>Traces & structured logs</h3></div><label className="trace-filter">Filter by trace ID<input value={traceFilter} onChange={(event) => setTraceFilter(event.target.value)} placeholder="All traces" /></label></div>{traceFilter && <button className="trace-link" onClick={() => setTraceFilter("")}>Clear trace filter</button>}<div className="telemetry-grid"><div><h4>Request & database spans</h4><div className="telemetry-scroll">{traces.length === 0 ? <p className="panel-empty">No matching spans.</p> : traces.slice(0, 50).map((span) => <article className="trace-row" key={span.id}><div><strong>{span.name}</strong><span>{Number(span.duration_ms).toFixed(2)} ms</span></div><button className="trace-link" onClick={() => setTraceFilter(span.trace_id)}>{span.trace_id}</button><small>{time(span.timestamp)} · {span.status}</small></article>)}</div></div><div><h4>Structured event log</h4><div className="telemetry-scroll">{logs.length === 0 ? <p className="panel-empty">No matching logs.</p> : logs.slice(0, 50).map((log) => <article className="log-row" key={log.id}><strong>{log.event}</strong><small>{time(log.timestamp)}</small><code>{JSON.stringify(log, null, 2)}</code></article>)}</div></div></div></section>
  </main>;
}
