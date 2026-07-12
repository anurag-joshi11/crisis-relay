export default function BlindspotCard({ blindspot, selected, decision, onSelect }) {
  const severityClass = blindspot.severity?.toLowerCase() || 'medium'
  const decisionClass = decision ? `decision-${decision.status.toLowerCase()}` : ''
  const statusLabel = decision?.status || 'OPEN'

  return (
    <button className={`card blindspot-card severity-${severityClass} ${decisionClass} ${selected ? 'selected' : ''}`} onClick={() => onSelect(blindspot)}>
      <div className="card-top">
        <strong>{blindspot.resource_id}</strong>
        <span className={`badge ${decision ? `decision-badge ${decisionClass}` : `severity-${severityClass}`}`}>{statusLabel}</span>
      </div>
      <p>{decision ? decision.summary : blindspot.reason}</p>
      {decision ? (
        <div className="decision-card-note">
          <span>Operation still unverified</span>
        </div>
      ) : (
        <div className="urgent-metric">
          <strong>{blindspot.minutes_in_state}</strong>
          <span>minutes unconfirmed</span>
        </div>
      )}
    </button>
  )
}
