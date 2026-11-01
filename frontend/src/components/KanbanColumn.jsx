import TaskCard from "./TaskCard";

export default function KanbanColumn({
  status,
  tasks,
  onDelete,
  onEdit,
  onStatusChange,
}) {
  return (
    <section className="kanban-column">
      <div className="column-heading">
        <span className={`status-dot status-${status.value}`} />
        <h2>{status.label}</h2>
        <span className="column-count">{tasks.length}</span>
      </div>

      <div className="column-content">
        {tasks.length === 0 ? (
          <div className="empty-column">No tasks here</div>
        ) : (
          tasks.map((task) => (
            <TaskCard
              key={task.id}
              task={task}
              onDelete={onDelete}
              onEdit={onEdit}
              onStatusChange={onStatusChange}
            />
          ))
        )}
      </div>
    </section>
  );
}
