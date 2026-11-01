export default function Header({ taskCount, onCreate }) {
  return (
    <header className="app-header">
      <div>
        <div className="brand-row">
          <span className="brand-mark">K</span>
          <span className="eyebrow">Kinufaktur operations</span>
        </div>
        <h1>AI Operations Command Center</h1>
        <p>A clear view of your work. A reliable path to recovery.</p>
      </div>

      <div className="header-actions">
        <span className="task-total">{taskCount} tasks</span>
        <button className="primary-button" type="button" onClick={onCreate}>
          <span aria-hidden="true">+</span> New task
        </button>
      </div>
    </header>
  );
}
