import { expect, it, vi } from "vitest";
import { API_BASE_URL, listTasks } from "./tasksApi";

it("decodes a successful JSON response", async () => {
  const tasks = [{ id: "demo-1", title: "Synthetic task" }];
  const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(tasks), {
    status: 200, headers: { "Content-Type": "application/json" },
  }));
  vi.stubGlobal("fetch", fetchMock);
  await expect(listTasks()).resolves.toEqual(tasks);
  expect(fetchMock).toHaveBeenCalledWith(`${API_BASE_URL}/tasks`, expect.objectContaining({
    headers: expect.objectContaining({
      traceparent: expect.stringMatching(/^00-[a-f0-9]{32}-[a-f0-9]{16}-01$/),
      "X-Request-ID": expect.any(String),
    }),
  }));
});

it("reports the backend's error message", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: "Task not found." }), {
    status: 404, headers: { "Content-Type": "application/json" },
  })));
  await expect(listTasks()).rejects.toThrow("Task not found.");
});

it("reports a useful connection error on network failure", async () => {
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
  await expect(listTasks()).rejects.toThrow("Could not connect to the Operations Command Center backend.");
});

it("keeps JSON headers while propagating a unique trace for each action", async () => {
  const { createTask } = await import("./tasksApi");
  const fetchMock = vi.fn().mockImplementation(async () => new Response("{}", {
    status: 201, headers: { "Content-Type": "application/json" },
  }));
  vi.stubGlobal("fetch", fetchMock);
  await createTask({ title: "Synthetic workflow" });
  await createTask({ title: "Second workflow" });
  const first = fetchMock.mock.calls[0][1];
  const second = fetchMock.mock.calls[1][1];
  expect(first.headers["Content-Type"]).toBe("application/json");
  expect(first.headers.traceparent).not.toBe(second.headers.traceparent);
  expect(first.headers["X-Request-ID"]).not.toBe(second.headers["X-Request-ID"]);
});
