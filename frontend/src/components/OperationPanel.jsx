import OperationCard from './OperationCard'

export default function OperationPanel({ operations = [] }) {
  return (
    <section className="panel operation-panel">
      <div className="panel-title-row">
        <div>
          <h2>Resource Snapshot</h2>
          <p className="panel-subtitle">Latest confirmed state for tracked resources.</p>
        </div>
        <span className="alert-count neutral">{operations.length}</span>
      </div>
      <div className="stack">
        {operations.map((operation) => <OperationCard key={operation.operation_id} operation={operation} />)}
      </div>
    </section>
  )
}
