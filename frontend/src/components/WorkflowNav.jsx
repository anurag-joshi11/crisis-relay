export default function WorkflowNav({ activeView, onChange }) {
  const views = [
    { id: 'overview', label: 'Operational Flow' },
    { id: 'command', label: 'Command Center' },
    { id: 'history', label: 'Audit Log' },
  ]

  return (
    <nav className="workflow-nav" aria-label="Incident command navigation">
      {views.map((view) => (
        <button
          key={view.id}
          className={activeView === view.id ? 'active' : ''}
          onClick={() => onChange(view.id)}
        >
          {view.label}
        </button>
      ))}
    </nav>
  )
}
