import { STATUSES } from "../constants";
import KanbanColumn from "./KanbanColumn";

export default function KanbanBoard({
  tasks,
  onDelete,
  onEdit,
  onStatusChange,
}) {
  return (
    <main className="kanban-board" aria-label="Operations Command Center Kanban board">
      {STATUSES.map((status) => (
        <KanbanColumn
          key={status.value}
          status={status}
          tasks={tasks.filter((task) => task.status === status.value)}
          onDelete={onDelete}
          onEdit={onEdit}
          onStatusChange={onStatusChange}
        />
      ))}
    </main>
  );
}
