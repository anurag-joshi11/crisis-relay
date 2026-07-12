export default function WorkflowNav({ activeView, onChange }) {
  const views = [
    { id: 'overview', label: 'Incident Overview' },
    { id: 'command', label: 'Command Center' },
    { id: 'history', label: 'Decision History' },
  ]

  return (
    <nav className="workflow-nav" aria-label="Command workflow">
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
