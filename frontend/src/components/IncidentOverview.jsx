const incidentCards = [
  {
    id: 'WF-001',
    name: 'Sector 4 Ridge Wildfire',
    type: 'Wildfire',
    status: 'Active command center',
    severity: 'Critical',
    description: 'Water-drop fulfilment and evacuation support are being monitored.',
    active: true,
  },
  {
    id: 'EQ-002',
    name: 'Downtown Structural Earthquake',
    type: 'Earthquake',
    status: 'Scenario not loaded',
    severity: 'Mock',
    description: 'Future workspace for collapsed structures, medical triage, and utility outages.',
    active: false,
  },
  {
    id: 'FL-003',
    name: 'River Basin Flood Response',
    type: 'Flood',
    status: 'Scenario not loaded',
    severity: 'Mock',
    description: 'Future workspace for rescue boats, shelter capacity, and road closures.',
    active: false,
  },
]

export default function IncidentOverview({ scenario, openIssues, decisionsCount, onOpenCommand }) {
  return (
    <main className="overview-page">
      <section className="panel overview-hero">
        <span className="section-label">Incident workspace</span>
        <h2>{scenario.id} / {scenario.name}</h2>
        <p>
          Each disaster gets its own command workspace. Reports feed active issues,
          issues drive decisions, and decisions are recorded for audit.
        </p>
        <div className="overview-metrics">
          <div>
            <span>Open issues</span>
            <strong>{openIssues}</strong>
          </div>
          <div>
            <span>Recorded decisions</span>
            <strong>{decisionsCount}</strong>
          </div>
          <div>
            <span>Mode</span>
            <strong>Mock safe</strong>
          </div>
        </div>
      </section>

      <section className="incident-grid">
        {incidentCards.map((incident) => (
          <article key={incident.id} className={`panel incident-card ${incident.active ? 'active' : 'locked'}`}>
            <div className="card-top">
              <strong>{incident.id}</strong>
              <span className={incident.active ? 'live-pill' : 'mock-pill'}>{incident.severity}</span>
            </div>
            <h3>{incident.name}</h3>
            <p>{incident.description}</p>
            <div className="incident-meta">
              <span>{incident.type}</span>
              <span>{incident.status}</span>
            </div>
            <button onClick={incident.active ? onOpenCommand : undefined} disabled={!incident.active}>
              {incident.active ? 'Open Command Center' : 'Not Loaded'}
            </button>
          </article>
        ))}
      </section>
    </main>
  )
}
