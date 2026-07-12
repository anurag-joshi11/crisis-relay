import OperationCard from './OperationCard'

export default function OperationPanel({ operations = [] }) {
  const activeOperations = operations.filter((operation) => operation.current_state || operation.last_state_change)

  return (
    <section className="panel operation-panel">
      <div className="panel-title-row">
        <div>
          <h2>Tracked Resources</h2>
          <p className="panel-subtitle">Latest confirmed operational state for each tracked resource.</p>
        </div>
        <span className="alert-count neutral">{activeOperations.length}</span>
      </div>
      <div className="stack">
        {activeOperations.length ? (
          activeOperations.map((operation) => <OperationCard key={operation.operation_id} operation={operation} />)
        ) : (
          <div className="empty-panel-note">
            <strong>No tracked resource states yet</strong>
            <p>Tracked resources appear here after the first confirmed operational state is received.</p>
          </div>
        )}
      </div>
    </section>
  )
}
