export default function DecisionHistoryPage({ scenario, decisions = [], onOpenCommand }) {
  return (
    <main className="history-page">
      <section className="panel history-hero">
        <span className="section-label">Operational audit</span>
        <h2>Audit Log</h2>
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
            <h3>No actions recorded yet</h3>
            <p>Approved and cancelled resource updates will appear here for operational review.</p>
            <button onClick={onOpenCommand}>Open Command Center</button>
          </div>
        )}
      </section>
    </main>
  )
}
