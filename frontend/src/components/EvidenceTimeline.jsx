export default function EvidenceTimeline({ timeline }) {
  if (!timeline) {
    return (
      <section className="timeline timeline-empty">
        <div className="timeline-heading">
          <span className="section-label">Evidence timeline</span>
          <h3>Waiting for an active issue</h3>
        </div>
        <div className="empty-panel-note timeline-empty-note">
          <strong>No evidence chain selected yet</strong>
          <p>Evidence appears after an active issue is selected from current incident operations.</p>
        </div>
      </section>
    )
  }

  return (
    <section className="timeline">
      <div className="timeline-heading">
        <span className="section-label">Evidence timeline</span>
        <h3>{timeline.operation_id}</h3>
      </div>
      <div className="timeline-track">
        {timeline.events.map((event, index) => (
          <div
            key={`${event.scenario_time || 'pending'}-${event.title}-${index}`}
            className={`timeline-node ${event.kind === 'missing_confirmation'
              ? 'missing-node'
              : event.kind === 'active_need'
                ? 'active-need-node'
                : event.kind === 'assumption'
                  ? 'assumption-node'
                  : event.kind === 'claim'
                    ? 'claim-node'
                    : 'confirmed-node'}`}
          >
            <div className="timeline-stamp">
              {event.scenario_time ? <span className="timeline-time">{event.scenario_time}</span> : <span className="missing-mark">?</span>}
              <strong>{event.title}</strong>
            </div>
            <p>{event.evidence}</p>
          </div>
        ))}
      </div>
    </section>
  )
}
