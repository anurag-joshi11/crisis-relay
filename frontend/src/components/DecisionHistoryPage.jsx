export default function DecisionHistoryPage({ scenario, decisions = [], onOpenCommand }) {
  return (
    <main className="history-page">
      <section className="panel history-hero">
        <span className="section-label">Audit trail</span>
        <h2>Decision History</h2>
        <p>{scenario.id} / {scenario.name}</p>
      </section>

      <section className="panel history-table">
        {decisions.length ? (
          <div className="history-table-list">
            {decisions.map((decision) => (
              <article
                key={`${decision.blindspot_id}-${decision.time}-${decision.status}`}
                className={`history-table-row decision-${decision.status.toLowerCase()}`}
              >
                <span>{decision.time}</span>
                <strong>{decision.status}</strong>
                <p>{decision.resource_id} / {decision.operation_id}</p>
                <p>{decision.summary}</p>
              </article>
            ))}
          </div>
        ) : (
          <div className="empty-history-page">
            <h3>No decisions recorded yet</h3>
            <p>Approve or cancel a resource update from the command center to populate this audit view.</p>
            <button onClick={onOpenCommand}>Open Command Center</button>
          </div>
        )}
      </section>
    </main>
  )
}
