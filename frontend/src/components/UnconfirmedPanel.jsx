import BlindspotCard from './BlindspotCard'

export default function UnconfirmedPanel({ blindspots = [], selectedBlindspot, decisionsByBlindspot = {}, onSelect }) {
  const severityRank = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 }
  const sortedBlindspots = [...blindspots].sort((left, right) => {
    const leftDecision = decisionsByBlindspot[left.blindspot_id]?.[0]
    const rightDecision = decisionsByBlindspot[right.blindspot_id]?.[0]
    if (Boolean(leftDecision) !== Boolean(rightDecision)) return leftDecision ? 1 : -1
    const severityDelta = (severityRank[left.severity] ?? 99) - (severityRank[right.severity] ?? 99)
    if (severityDelta !== 0) return severityDelta
    return (right.minutes_in_state || 0) - (left.minutes_in_state || 0)
  })
  const openCount = blindspots.filter((blindspot) => !decisionsByBlindspot[blindspot.blindspot_id]?.length).length

  return (
    <section className="panel alert-panel">
      <div className="panel-title-row">
        <div>
          <h2>Active Issues</h2>
          <p className="panel-subtitle">Unconfirmed operations needing a decision.</p>
        </div>
        <span className="alert-count">{openCount} open</span>
      </div>
      <div className="stack">
        {sortedBlindspots.length ? (
          sortedBlindspots.map((blindspot) => (
            <BlindspotCard
              key={blindspot.blindspot_id}
              blindspot={blindspot}
              selected={selectedBlindspot?.blindspot_id === blindspot.blindspot_id}
              decision={decisionsByBlindspot[blindspot.blindspot_id]?.[0]}
              onSelect={onSelect}
            />
          ))
        ) : (
          <div className="empty-panel-note">
            <strong>No active issue yet</strong>
            <p>Keep advancing field reports until an operation stays unconfirmed long enough to need command attention.</p>
          </div>
        )}
      </div>
    </section>
  )
}
