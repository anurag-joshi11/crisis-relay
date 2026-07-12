export default function DecisionHistory({ blindspot, decisions = [] }) {
  return (
    <section className="panel history-panel">
      <div className="panel-title-row">
        <div>
          <h2>Decision History</h2>
          <p className="panel-subtitle">
            {blindspot ? `${blindspot.operation_id} / ${blindspot.resource_id}` : 'Select an issue to inspect decisions.'}
          </p>
        </div>
      </div>
      {decisions.length ? (
        <div className="history-list">
          {decisions.map((decision) => (
            <article key={`${decision.time}-${decision.status}`} className={`history-item decision-${decision.status.toLowerCase()}`}>
              <span>{decision.time}</span>
              <strong>{decision.status}</strong>
              <p>{decision.summary}</p>
            </article>
          ))}
        </div>
      ) : (
        <p className="empty-history">No decisions recorded for this issue yet.</p>
      )}
    </section>
  )
}
