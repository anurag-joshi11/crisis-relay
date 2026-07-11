export default function EvidenceTimeline({ timeline }) {
  if (!timeline) return null
  return (
    <section className="timeline">
      <h3>{timeline.operation_id} - Operational Timeline</h3>
      <div className="timeline-row">
        {timeline.events.map((event) => (
          <div key={`${event.scenario_time}-${event.new_state}`} className="timeline-event">
            <div className="timeline-time">{event.scenario_time}</div>
            <div className="timeline-state">{event.new_state}</div>
            <p>{event.evidence}</p>
          </div>
        ))}
        <div className="timeline-gap">?</div>
        <div className="timeline-note">{timeline.missing_confirmation}</div>
      </div>
    </section>
  )
}

