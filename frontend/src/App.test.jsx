import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import { listTasks, updateTask } from "./api/tasksApi";

vi.mock("./api/tasksApi", () => ({
  listTasks: vi.fn(),
  createTask: vi.fn(),
  updateTask: vi.fn(),
  deleteTask: vi.fn(),
}));

vi.mock("./components/OperationsDashboard", () => ({ default: () => <div>Operations overview panel</div> }));

const task = {
  id: "demo-1", title: "Map invoice intake", description: "Synthetic request",
  category: "AI Automation", priority: "Medium", status: "incoming",
};

function column(label) {
  return screen.getByRole("heading", { name: label }).closest("section");
}

beforeEach(() => {
  vi.resetAllMocks();
  listTasks.mockResolvedValue([task]);
});

describe("Kanban board", () => {
  it("renders tasks in their appropriate columns", async () => {
    listTasks.mockResolvedValue([
      task, { ...task, id: "demo-2", title: "Review sources", status: "planned" },
    ]);
    render(<App />);
    await userEvent.click(screen.getByRole("button", { name: "Task workspace" }));
    await screen.findByText(task.title);
    expect(within(column("Incoming")).getByText(task.title)).toBeInTheDocument();
    expect(within(column("Planned")).getByText("Review sources")).toBeInTheDocument();
    expect(within(column("Done")).queryByRole("article")).not.toBeInTheDocument();
  });

  it("shows a useful error when loading fails", async () => {
    listTasks.mockRejectedValue(new Error("offline"));
    render(<App />);
    await userEvent.click(screen.getByRole("button", { name: "Task workspace" }));
    expect(await screen.findByText("Tasks could not be loaded.")).toBeInTheDocument();
    expect(screen.queryByText("Loading tasks…")).not.toBeInTheDocument();
  });

  it("calls the API and moves a task on a successful status change", async () => {
    const user = userEvent.setup();
    updateTask.mockResolvedValue({ ...task, status: "planned" });
    render(<App />);
    await userEvent.click(screen.getByRole("button", { name: "Task workspace" }));
    await screen.findByText(task.title);
    await user.selectOptions(within(column("Incoming")).getByRole("combobox"), "planned");
    expect(updateTask).toHaveBeenCalledWith(task.id, { status: "planned" });
    expect(await screen.findByText("Moved to Planned.")).toBeInTheDocument();
    expect(within(column("Planned")).getByText(task.title)).toBeInTheDocument();
    expect(within(column("Incoming")).queryByText(task.title)).not.toBeInTheDocument();
  });

  it("restores the previous board after a failed optimistic status change", async () => {
    const user = userEvent.setup();
    let rejectUpdate;
    updateTask.mockReturnValue(new Promise((_, reject) => { rejectUpdate = reject; }));
    render(<App />);
    await userEvent.click(screen.getByRole("button", { name: "Task workspace" }));
    await screen.findByText(task.title);
    await user.selectOptions(within(column("Incoming")).getByRole("combobox"), "done");
    expect(updateTask).toHaveBeenCalledWith(task.id, { status: "done" });
    expect(within(column("Done")).getByText(task.title)).toBeInTheDocument();
    rejectUpdate(new Error("Status could not be saved."));
    await screen.findByText("Status could not be saved.");
    await waitFor(() => expect(within(column("Incoming")).getByText(task.title)).toBeInTheDocument());
    expect(within(column("Done")).queryByText(task.title)).not.toBeInTheDocument();
  });
});
