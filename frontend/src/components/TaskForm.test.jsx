import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it, vi } from "vitest";
import TaskForm from "./TaskForm";

it("does not submit when either required field is empty", async () => {
  const user = userEvent.setup();
  const onSubmit = vi.fn();
  render(<TaskForm task={null} isSaving={false} onCancel={vi.fn()} onSubmit={onSubmit} />);
  await user.click(screen.getByRole("button", { name: "Create task" }));
  expect(screen.getByLabelText("Title")).toBeInvalid();
  expect(onSubmit).not.toHaveBeenCalled();
  await user.type(screen.getByLabelText("Title"), "Synthetic task");
  await user.click(screen.getByRole("button", { name: "Create task" }));
  expect(screen.getByLabelText("Description")).toBeInvalid();
  expect(onSubmit).not.toHaveBeenCalled();
});

it("submits normalized data and the selected category, priority and status", async () => {
  const user = userEvent.setup();
  const onSubmit = vi.fn();
  render(<TaskForm task={null} isSaving={false} onCancel={vi.fn()} onSubmit={onSubmit} />);
  await user.type(screen.getByLabelText("Title"), "  Map sources  ");
  await user.type(screen.getByLabelText("Description"), "  Synthetic description  ");
  await user.selectOptions(screen.getByLabelText("Category"), "Data");
  await user.selectOptions(screen.getByLabelText("Priority"), "High");
  await user.selectOptions(screen.getByLabelText("Status"), "planned");
  await user.click(screen.getByRole("button", { name: "Create task" }));
  expect(onSubmit).toHaveBeenCalledExactlyOnceWith({
    title: "Map sources", description: "Synthetic description",
    category: "Data", priority: "High", status: "planned",
  });
});
