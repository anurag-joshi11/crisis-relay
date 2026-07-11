import BlindspotCard from './BlindspotCard'

export default function UnconfirmedPanel({ blindspots = [], selectedBlindspot, onSelect }) {
  return (
    <section className="panel">
      <h2>Unconfirmed Operations</h2>
      <div className="stack">
        {blindspots.map((blindspot) => (
          <BlindspotCard
            key={blindspot.blindspot_id}
            blindspot={blindspot}
            selected={selectedBlindspot?.blindspot_id === blindspot.blindspot_id}
            onSelect={onSelect}
          />
        ))}
      </div>
    </section>
  )
}

