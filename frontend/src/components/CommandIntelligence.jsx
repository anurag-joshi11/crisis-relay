import EvidenceTimeline from './EvidenceTimeline'

export default function CommandIntelligence({ blindspot, timeline, dispatch, onDraft }) {
  return (
    <section className="panel command">
      <div className="command-copy">
        <h2>Command Intelligence</h2>
        {blindspot ? <p>{blindspot.reason}</p> : <p>Select a blindspot to inspect latest confirmed state and missing confirmation.</p>}
        {timeline ? (
          <>
            <p className="muted">Latest confirmed resource state: {timeline.events[timeline.events.length - 1].new_state}</p>
            <p className="muted">Fulfilment: NOT VERIFIED</p>
          </>
        ) : null}
      </div>
      <EvidenceTimeline timeline={timeline} />
      <button onClick={onDraft} disabled={!blindspot}>DRAFT STATUS REQUEST</button>
      {dispatch ? <div className="draft-card"><strong>{dispatch.approval_status}</strong><p>{dispatch.ai_draft}</p></div> : null}
    </section>
  )
}

