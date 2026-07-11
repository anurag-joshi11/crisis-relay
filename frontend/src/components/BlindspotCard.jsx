export default function BlindspotCard({ blindspot, selected, onSelect }) {
  return (
    <button className={`card blindspot-card ${selected ? 'selected' : ''}`} onClick={() => onSelect(blindspot)}>
      <div className="card-top">
        <strong>{blindspot.resource_id}</strong>
        <span>{blindspot.severity}</span>
      </div>
      <p>{blindspot.reason}</p>
      <p className="muted">{blindspot.minutes_in_state} minutes in state</p>
    </button>
  )
}

