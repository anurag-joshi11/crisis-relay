import OperationCard from './OperationCard'

export default function OperationPanel({ operations = [] }) {
  return (
    <section className="panel">
      <h2>Operational State</h2>
      <div className="stack">
        {operations.map((operation) => <OperationCard key={operation.operation_id} operation={operation} />)}
      </div>
    </section>
  )
}

