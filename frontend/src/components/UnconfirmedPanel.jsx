import BlindspotCard from './BlindspotCard'

export default function UnconfirmedPanel({ blindspots = [], selectedBlindspot, decisionsByBlindspot = {}, onSelect }) {
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
        {blindspots.length ? (
          blindspots.map((blindspot) => (
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
