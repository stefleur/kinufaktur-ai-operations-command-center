// Independent defaults: never contact the original application's infrastructure.
export const API_BASE_URL = import.meta.env?.VITE_API_BASE_URL || "http://localhost:8000";

function correlationHeaders() {
  const hex = (length) => Array.from(crypto.getRandomValues(new Uint8Array(length)), (value) => value.toString(16).padStart(2, "0")).join("");
  return { traceparent: `00-${hex(16)}-${hex(8)}-01`, "X-Request-ID": crypto.randomUUID() };
}

export async function request(path, options = {}) {
  let response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers: { ...correlationHeaders(), ...options.headers } });
  } catch {
    throw new Error("Could not connect to the Operations Command Center backend.");
  }

  const contentType = response.headers.get("content-type") ?? "";
  const data = contentType.includes("application/json")
    ? await response.json()
    : null;

  if (!response.ok) {
    const message =
      typeof data?.detail === "string"
        ? data.detail
        : `Request failed with status ${response.status}.`;
    throw new Error(message);
  }

  return data;
}

function jsonRequest(method, body) {
  return {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  };
}

export function listTasks() {
  return request("/tasks");
}

export function getTask(taskId) {
  return request(`/tasks/${encodeURIComponent(taskId)}`);
}

export function createTask(taskInput) {
  return request("/tasks", jsonRequest("POST", taskInput));
}

export function updateTask(taskId, changes) {
  return request(
    `/tasks/${encodeURIComponent(taskId)}`,
    jsonRequest("PATCH", changes),
  );
}

export function deleteTask(taskId) {
  return request(`/tasks/${encodeURIComponent(taskId)}`, { method: "DELETE" });
}
