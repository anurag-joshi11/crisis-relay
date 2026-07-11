export default function OperationCard({ operation }) {
  return (
    <article className="card op-card">
      <div className="card-top">
        <strong>{operation.operation_type.replaceAll('_', ' ')}</strong>
        <span>{operation.priority}</span>
      </div>
      <p>{operation.resource_id} · {operation.location}</p>
      <p className="muted">Confirmed state: {operation.current_state}</p>
      <p className="muted">Last change: {operation.last_state_change}</p>
    </article>
  )
}

