import EvidenceTimeline from './EvidenceTimeline'
import { resolveAudioUrl } from '../audioUrl'

export default function CommandIntelligence({ blindspot, timeline, dispatch, decision, onDraft }) {
  const isApproved = decision?.status === 'APPROVED'
  const isRejected = decision?.status === 'REJECTED'
  const headerStatus = decision?.status || blindspot?.severity
  const audioUrl = resolveAudioUrl(dispatch?.audio_url)
  const toneClass = decision
    ? `decision-${decision.status.toLowerCase()}`
    : blindspot?.severity
      ? `severity-${blindspot.severity.toLowerCase()}`
      : ''
  const commandTitle = blindspot?.severity === 'CRITICAL'
    ? 'Critical Decision'
    : blindspot?.severity === 'HIGH'
      ? 'High Priority Decision'
      : 'Priority Decision'
  const followUpLabel = isApproved ? 'REQUEST UPDATED CHECK-IN' : isRejected ? 'CREATE NEW REQUEST' : 'REQUEST UPDATE'

  return (
    <section className="panel command">
      <div className="command-header">
        <div>
          <h2>{commandTitle}</h2>
          <p className="muted">Review the selected issue and decide whether to request an update.</p>
        </div>
        {headerStatus ? (
          <span className={`badge ${decision ? `decision-badge decision-${decision.status.toLowerCase()}` : `severity-${blindspot.severity.toLowerCase()}`}`}>
            {headerStatus}
          </span>
        ) : null}
      </div>

      <div className="command-grid">
        <div className={`assessment-box ${toneClass}`}>
          <span className="section-label">Assessment</span>
          {blindspot ? (
            <div className={`action-headline ${toneClass}`}>
              {isApproved ? 'Update approved' : isRejected ? 'Update rejected' : `${blindspot.resource_id} needs status check`}
            </div>
          ) : null}
          {blindspot ? (
            <p className="assessment-text">
              {isApproved
                ? `The operator approved an update request. ${blindspot.resource_id} remains unverified until a new field report confirms arrival or completion.`
                : isRejected
                  ? `The operator cancelled the update request. No broadcast was sent. ${blindspot.resource_id} remains unverified.`
                  : blindspot.reason}
            </p>
          ) : <p>Field reports have not produced a selectable active issue yet. Advance the scenario, then choose an issue from the left rail.</p>}
        </div>

        <div className={`action-box ${toneClass}`}>
          <span className="section-label">{decision ? 'Decision recorded' : 'Decision'}</span>
          {isApproved ? (
            <>
              <strong className="decision-title">Approved</strong>
              <p>Resource update request was approved. Awaiting field confirmation from the resource.</p>
              <div className="decision-meta">
                <span>Solana: {dispatch?.solana_status || 'PENDING_SYNC'}</span>
                {dispatch?.solana_error ? <span>Solana error: {dispatch.solana_error}</span> : null}
                <span>Audio: {dispatch?.audio_status || (dispatch?.audio_url ? 'AVAILABLE' : 'UNAVAILABLE')}</span>
                {dispatch?.audio_error ? <span>Audio error: {dispatch.audio_error}</span> : null}
              </div>
              {audioUrl ? (
                <div className="audio-review">
                  <div>
                    <strong>Generated voice message</strong>
                    <span>Listen before treating this message as broadcast-ready. If the issue remains open, generate a fresh follow-up request.</span>
                  </div>
                  <audio controls src={audioUrl}>
                    Your browser does not support audio playback.
                  </audio>
                </div>
              ) : null}
              <button onClick={onDraft} disabled={!blindspot}>{followUpLabel}</button>
            </>
          ) : isRejected ? (
            <>
              <strong className="decision-title">Rejected</strong>
              <p>Request cancelled. Nothing was broadcast.</p>
              <button onClick={onDraft} disabled={!blindspot}>{followUpLabel}</button>
            </>
          ) : (
            <>
              <p>{blindspot ? 'Ask the resource for current status before assuming arrival or completion.' : 'A resource update can be requested once an active issue is selected.'}</p>
              <button onClick={onDraft} disabled={!blindspot}>{followUpLabel}</button>
            </>
          )}
        </div>
      </div>

      <EvidenceTimeline timeline={timeline} />
    </section>
  )
}
