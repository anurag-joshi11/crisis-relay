export default function EvidenceTimeline({ timeline }) {
  if (!timeline) return null

  const missingLabel = timeline.missing_confirmation === 'ARRIVAL_OR_FULFILMENT'
    ? 'Missing confirmation'
    : timeline.missing_confirmation

  return (
    <section className="timeline">
      <div className="timeline-heading">
        <span className="section-label">Evidence timeline</span>
        <h3>{timeline.operation_id}</h3>
      </div>
      <div className="timeline-track">
        {timeline.events.map((event) => (
          <div key={`${event.scenario_time}-${event.new_state}`} className="timeline-node confirmed-node">
            <div className="timeline-stamp">
              <span className="timeline-time">{event.scenario_time}</span>
              <strong>{event.new_state}</strong>
            </div>
            <p>{event.evidence}</p>
          </div>
        ))}
        <div className="timeline-node missing-node">
          <div className="timeline-stamp">
            <span className="missing-mark">?</span>
            <strong>{missingLabel}</strong>
          </div>
          <p>No arrival or fulfilment confirmation has been received.</p>
        </div>
        {timeline.related_active_need ? (
          <div className="timeline-node active-need-node">
            <div className="timeline-stamp">
              <span className="timeline-time">{timeline.related_active_need.scenario_time}</span>
              <strong>Active need repeated</strong>
            </div>
            <p>{timeline.related_active_need.evidence}</p>
          </div>
        ) : null}
      </div>
    </section>
  )
}
