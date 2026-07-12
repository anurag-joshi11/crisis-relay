import EvidenceTimeline from './EvidenceTimeline'

export default function CommandIntelligence({ blindspot, timeline, dispatch, decision, onDraft }) {
  const isApproved = decision?.status === 'APPROVED'
  const isRejected = decision?.status === 'REJECTED'
  const headerStatus = decision?.status || blindspot?.severity
  const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:8000'
  const audioUrl = dispatch?.audio_url
    ? dispatch.audio_url.startsWith('http')
      ? dispatch.audio_url
      : `${apiBase}${dispatch.audio_url}`
    : null

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
              <p>Resource update request was approved. Awaiting field confirmation from the resource.</p>
              <div className="decision-meta">
                <span>Solana: {dispatch?.solana_status || 'PENDING_SYNC'}</span>
                {dispatch?.solana_signature ? <span>Signature: {dispatch.solana_signature}</span> : null}
                {dispatch?.solana_error ? <span>Solana error: {dispatch.solana_error}</span> : null}
                <span>Audio: {dispatch?.audio_status || (dispatch?.audio_url ? 'AVAILABLE' : 'UNAVAILABLE')}</span>
                {dispatch?.audio_error ? <span>Audio error: {dispatch.audio_error}</span> : null}
              </div>
              {audioUrl ? (
                <div className="audio-review">
                  <div>
                    <strong>Generated voice message</strong>
                    <span>Listen before treating this broadcast as demo-ready.</span>
                  </div>
                  <audio controls src={audioUrl}>
                    Your browser does not support audio playback.
                  </audio>
                  <a href={audioUrl} target="_blank" rel="noreferrer">Open MP3</a>
                </div>
              ) : null}
              <button onClick={onDraft} disabled={!blindspot}>SEND FOLLOW-UP UPDATE</button>
            </>
          ) : isRejected ? (
            <>
              <strong className="decision-title">Rejected</strong>
              <p>Request cancelled. Nothing was broadcast.</p>
              <button onClick={onDraft} disabled={!blindspot}>CREATE NEW REQUEST</button>
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
