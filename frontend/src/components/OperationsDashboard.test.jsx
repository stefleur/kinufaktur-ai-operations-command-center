import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";
import OperationsDashboard from "./OperationsDashboard";
import { request } from "../api/tasksApi";

vi.mock("../api/tasksApi", () => ({ request: vi.fn() }));
const incident = {
  id: "incident-1", timestamp: Date.parse("2026-11-01T10:00:00Z") / 1000, trace_id: "a".repeat(32),
  status: "resolved", diagnosis: "Demo dependency failed", action: "restore_demo_dependency",
  result: "Health verified", timeline: [
    { event: "agent_activated", timestamp: "2026-11-01T10:00:00Z" },
    { event: "recovery_verified", timestamp: "2026-11-01T10:00:01Z", tool: "health_check", result: "healthy" },
  ],
};
let incidents;
beforeEach(() => {
  incidents = [];
  request.mockReset();
  request.mockImplementation(async (path) => {
    if (path === "/ops/overview") return {
      health: { status: "healthy", dependency: { status: "healthy" } },
      metrics: { request_count: 12, error_count: 1, error_rate: 1 / 12, average_latency_ms: 3.2, workflow_count: 2, failed_workflow_count: 1 },
      incidents, alerts: incidents.length ? [{ id: "alert-1", rule: "workflow_failure", state: "resolved", threshold: 1, timestamp: incident.timestamp }] : [],
    };
    if (path === "/ops/telemetry") return { traces: [{ id: 1, trace_id: incident.trace_id, name: "POST /workflows/run", timestamp: incident.timestamp, duration_ms: 12, status: "ERROR" }], logs: [{ id: 1, trace_id: incident.trace_id, event: "workflow_failed", timestamp: incident.timestamp }] };
    if (path === "/ops/demo/fault") return { status: "faulted" };
    if (path === "/workflows/run") { incidents = [incident]; throw new Error("Demo workflow dependency unavailable."); }
    throw new Error(`Unexpected request ${path}`);
  });
});

it("renders actual health, metrics and trace signals", async () => {
  render(<OperationsDashboard />);
  expect(await screen.findByText("12")).toBeInTheDocument();
  expect(screen.getByText("8.3%")).toBeInTheDocument();
  expect(screen.getByText("3.2 ms")).toBeInTheDocument();
  expect(screen.getByText("workflow_failed")).toBeInTheDocument();
  expect(screen.getByText("POST /workflows/run")).toBeInTheDocument();
  expect(screen.getAllByText(new Date(incident.timestamp * 1000).toLocaleString()).length).toBeGreaterThan(0);
});

it("displays backend failure and recorded agent timeline, then filters correlated telemetry", async () => {
  render(<OperationsDashboard />);
  await screen.findByText("12");
  fireEvent.click(screen.getByRole("button", { name: "Inject demo fault" }));
  await screen.findByText(/isolated demo dependency is faulted/);
  fireEvent.click(screen.getByRole("button", { name: "Run workflow" }));
  await screen.findByText(/Workflow failed: Demo workflow dependency unavailable/);
  fireEvent.click(await screen.findByRole("button", { name: /Demo dependency failed/ }));
  expect(screen.getByText("recovery_verified")).toBeInTheDocument();
  expect(screen.getByText("restore_demo_dependency")).toBeInTheDocument();
  expect(screen.getByLabelText("Filter by trace ID")).toHaveValue(incident.trace_id);
  fireEvent.change(screen.getByLabelText("Filter by trace ID"), { target: { value: "not-matching" } });
  expect(screen.getByText("No matching spans.")).toBeInTheDocument();
});

it("reports unavailable telemetry honestly", async () => {
  request.mockRejectedValue(new Error("Connection unavailable"));
  render(<OperationsDashboard />);
  await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("Connection unavailable"));
});
