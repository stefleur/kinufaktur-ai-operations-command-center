import { useEffect, useState } from "react";

import {
  createTask,
  deleteTask,
  listTasks,
  updateTask,
} from "./api/tasksApi";
import OperationsDashboard from "./components/OperationsDashboard";
import Header from "./components/Header";
import KanbanBoard from "./components/KanbanBoard";
import TaskForm from "./components/TaskForm";
import { getStatusLabel } from "./constants";

export default function App() {
  const [view, setView] = useState("operations");
  const [tasks, setTasks] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [formTask, setFormTask] = useState(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadTasks() {
      try {
        setTasks(await listTasks());
      } catch {
        setError("Tasks could not be loaded.");
      } finally {
        setIsLoading(false);
      }
    }

    loadTasks();
  }, []);

  function showMessage(nextMessage) {
    setError("");
    setMessage(nextMessage);
    window.setTimeout(() => setMessage(""), 2200);
  }

  function openCreateForm() {
    setView("tasks");
    setFormTask(null);
    setIsFormOpen(true);
  }

  function openEditForm(task) {
    setFormTask(task);
    setIsFormOpen(true);
  }

  async function saveTask(formData) {
    setIsSaving(true);
    setError("");

    try {
      if (formTask) {
        const savedTask = await updateTask(formTask.id, formData);
        setTasks((current) =>
          current.map((task) => (task.id === savedTask.id ? savedTask : task)),
        );
        showMessage("Task updated.");
      } else {
        const savedTask = await createTask(formData);
        setTasks((current) => [savedTask, ...current]);
        showMessage("Task created.");
      }

      setIsFormOpen(false);
    } catch (requestError) {
      setError(requestError.message || "The task could not be saved.");
    } finally {
      setIsSaving(false);
    }
  }

  async function changeStatus(task, status) {
    const previousTasks = tasks;
    setTasks((current) =>
      current.map((item) => (item.id === task.id ? { ...item, status } : item)),
    );

    try {
      const savedTask = await updateTask(task.id, { status });
      setTasks((current) =>
        current.map((item) => (item.id === savedTask.id ? savedTask : item)),
      );
      showMessage(`Moved to ${getStatusLabel(status)}.`);
    } catch (requestError) {
      setTasks(previousTasks);
      setError(requestError.message || "The task could not be moved.");
    }
  }

  async function removeTask(task) {
    const confirmed = window.confirm(`Delete “${task.title}”?`);
    if (!confirmed) return;

    try {
      await deleteTask(task.id);
      setTasks((current) => current.filter((item) => item.id !== task.id));
      showMessage("Task deleted.");
    } catch (requestError) {
      setError(requestError.message || "The task could not be deleted.");
    }
  }

  return (
    <div className="app-shell">
      <Header taskCount={tasks.length} onCreate={openCreateForm} />

      <nav className="view-tabs" aria-label="Workspace">
        <button className={view === "operations" ? "active" : ""} onClick={() => setView("operations")}>Operations overview</button>
        <button className={view === "tasks" ? "active" : ""} onClick={() => setView("tasks")}>Task workspace</button>
      </nav>
      {view === "operations" && <OperationsDashboard />}
      {message && <div className="notice success">{message}</div>}
      {error && <div className="notice error">{error}</div>}

      <div hidden={view !== "tasks"}>
      {isLoading ? (
        <div className="loading-state">Loading tasks…</div>
      ) : (
        <KanbanBoard
          tasks={tasks}
          onDelete={removeTask}
          onEdit={openEditForm}
          onStatusChange={changeStatus}
        />
      )}

      </div>
      {isFormOpen && (
        <TaskForm
          task={formTask}
          isSaving={isSaving}
          onCancel={() => setIsFormOpen(false)}
          onSubmit={saveTask}
        />
      )}
    </div>
  );
}
