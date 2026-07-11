import EvidenceTimeline from './EvidenceTimeline'

export default function CommandIntelligence({ blindspot, timeline, dispatch, decision, onDraft }) {
  const isApproved = decision?.status === 'APPROVED'
  const isRejected = decision?.status === 'REJECTED'
  const headerStatus = decision?.status || blindspot?.severity

  return (
    <section className="panel command">
      <div className="command-header">
        <div>
          <h2>Priority Decision</h2>
          <p className="muted">Review the selected issue and decide whether to request a resource update.</p>
        </div>
        {headerStatus ? (
          <span className={`badge ${decision ? `decision-badge decision-${decision.status.toLowerCase()}` : `severity-${blindspot.severity.toLowerCase()}`}`}>
            {headerStatus}
          </span>
        ) : null}
      </div>

      <div className="command-grid">
        <div className="assessment-box">
          <span className="section-label">Assessment</span>
          {blindspot ? (
            <div className="action-headline">
              {isApproved ? 'Status request approved' : isRejected ? 'Status request rejected' : `${blindspot.resource_id} needs status check`}
            </div>
          ) : null}
          {blindspot ? (
            <p className="assessment-text">
              {isApproved
                ? `The operator approved a resource update request. ${blindspot.resource_id} remains unverified until a new field report confirms arrival or completion.`
                : isRejected
                  ? `The operator cancelled the resource update request. No broadcast was sent. ${blindspot.resource_id} remains unverified.`
                  : blindspot.reason}
            </p>
          ) : <p>Select an issue to inspect latest confirmed state and missing confirmation.</p>}
        </div>

        <div className={`action-box ${decision ? `decision-${decision.status.toLowerCase()}` : ''}`}>
          <span className="section-label">{decision ? 'Decision recorded' : 'Decision'}</span>
          {isApproved ? (
            <>
              <strong className="decision-title">Approved</strong>
              <p>Mock broadcast complete. Awaiting field confirmation.</p>
              <div className="decision-meta">
                <span>Solana: {dispatch?.solana_status || 'PENDING_SYNC'}</span>
                <span>Audio: {dispatch?.audio_url ? 'AVAILABLE' : 'NOT GENERATED'}</span>
              </div>
              <button onClick={onDraft} disabled={!blindspot}>REQUEST NEW UPDATE</button>
            </>
          ) : isRejected ? (
            <>
              <strong className="decision-title">Rejected</strong>
              <p>Request cancelled. Nothing was broadcast.</p>
              <button onClick={onDraft} disabled={!blindspot}>REQUEST NEW UPDATE</button>
            </>
          ) : (
            <>
              <p>Ask the resource for current status before assuming arrival or completion.</p>
              <button onClick={onDraft} disabled={!blindspot}>REQUEST RESOURCE UPDATE</button>
            </>
          )}
        </div>
      </div>

      <EvidenceTimeline timeline={timeline} />
    </section>
  )
}
