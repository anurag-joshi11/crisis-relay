export default function OperationCard({ operation }) {
  const severityClass = operation.priority?.toLowerCase() || 'medium'

  return (
    <article className={`card op-card severity-${severityClass}`}>
      <div className="card-top">
        <strong>{operation.operation_type.replaceAll('_', ' ')}</strong>
        <span className={`badge severity-${severityClass}`}>{operation.priority}</span>
      </div>
      <p className="resource-line">{operation.resource_id} - {operation.location}</p>
      <div className="chip-row">
        <span className="chip state-chip">{operation.current_state}</span>
        <span className="chip">{operation.fulfilled ? 'FULFILLED' : 'UNFULFILLED'}</span>
        <span className="chip">LAST {operation.last_state_change}</span>
      </div>
    </article>
  )
}
