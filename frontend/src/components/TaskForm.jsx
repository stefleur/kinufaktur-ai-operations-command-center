import { useEffect, useState } from "react";

import { CATEGORIES, PRIORITIES, STATUSES } from "../constants";

const EMPTY_TASK = {
  title: "",
  description: "",
  category: CATEGORIES[0],
  priority: PRIORITIES[1],
  status: STATUSES[0].value,
};

export default function TaskForm({ task, isSaving, onCancel, onSubmit }) {
  const [formData, setFormData] = useState(EMPTY_TASK);

  useEffect(() => {
    setFormData(task ? { ...task } : EMPTY_TASK);
  }, [task]);

  function handleChange(event) {
    const { name, value } = event.target;
    setFormData((current) => ({ ...current, [name]: value }));
  }

  function handleSubmit(event) {
    event.preventDefault();
    onSubmit({
      title: formData.title.trim(),
      description: formData.description.trim(),
      category: formData.category,
      priority: formData.priority,
      status: formData.status,
    });
  }

  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={onCancel}>
      <section
        className="task-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="task-form-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="modal-heading">
          <div>
            <span className="eyebrow">Task details</span>
            <h2 id="task-form-title">{task ? "Edit task" : "Create task"}</h2>
          </div>
          <button className="close-button" type="button" onClick={onCancel}>
            <span aria-hidden="true">×</span>
            <span className="sr-only">Close</span>
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <label>
            Title
            <input
              autoFocus
              required
              maxLength="120"
              name="title"
              value={formData.title}
              onChange={handleChange}
              placeholder="What needs to happen?"
            />
          </label>

          <label>
            Description
            <textarea
              required
              maxLength="500"
              name="description"
              rows="4"
              value={formData.description}
              onChange={handleChange}
              placeholder="Add a short, useful description"
            />
          </label>

          <div className="form-grid">
            <label>
              Category
              <select name="category" value={formData.category} onChange={handleChange}>
                {CATEGORIES.map((category) => (
                  <option key={category}>{category}</option>
                ))}
              </select>
            </label>

            <label>
              Priority
              <select name="priority" value={formData.priority} onChange={handleChange}>
                {PRIORITIES.map((priority) => (
                  <option key={priority}>{priority}</option>
                ))}
              </select>
            </label>

            <label>
              Status
              <select name="status" value={formData.status} onChange={handleChange}>
                {STATUSES.map((status) => (
                  <option key={status.value} value={status.value}>
                    {status.label}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div className="modal-actions">
            <button className="secondary-button" type="button" onClick={onCancel}>
              Cancel
            </button>
            <button className="primary-button" type="submit" disabled={isSaving}>
              {isSaving ? "Saving…" : task ? "Save changes" : "Create task"}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}
