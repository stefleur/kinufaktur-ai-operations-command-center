import { STATUSES } from "../constants";

export default function TaskCard({ task, onDelete, onEdit, onStatusChange }) {
  return (
    <article className="task-card">
      <div className="card-topline">
        <span className={`priority priority-${task.priority.toLowerCase()}`}>
          {task.priority}
        </span>
        <div className="card-actions">
          <button
            className="icon-button"
            type="button"
            aria-label={`Edit ${task.title}`}
            onClick={() => onEdit(task)}
          >
            Edit
          </button>
          <button
            className="icon-button danger"
            type="button"
            aria-label={`Delete ${task.title}`}
            onClick={() => onDelete(task)}
          >
            Delete
          </button>
        </div>
      </div>

      <h3>{task.title}</h3>
      <p>{task.description}</p>
      <span className="category">{task.category}</span>

      <label className="status-control">
        <span>Move to</span>
        <select
          value={task.status}
          onChange={(event) => onStatusChange(task, event.target.value)}
        >
          {STATUSES.map((status) => (
            <option key={status.value} value={status.value}>
              {status.label}
            </option>
          ))}
        </select>
      </label>
    </article>
  );
}
