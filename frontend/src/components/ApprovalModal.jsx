export default function ApprovalModal({ dispatch, text, setText, onReject, onApprove, onPreviewAudio, onClose }) {
  if (!dispatch) return null

  const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:8000'
  const audioUrl = dispatch.audio_url
    ? dispatch.audio_url.startsWith('http')
      ? dispatch.audio_url
      : `${apiBase}${dispatch.audio_url}`
    : null
  const previewMatchesText = Boolean(audioUrl && dispatch.audio_preview_text === text)
  const canApprove = Boolean(text.trim() && previewMatchesText && dispatch.audio_status === 'AVAILABLE')

  return (
    <div className="modal-backdrop">
      <div className="modal">
        <div className="card-top">
          <h3>Validate Voice Message</h3>
          <span>{dispatch.dispatch_id}</span>
        </div>
        <p className="muted">Edit the exact message, generate the voice preview, listen to it, then approve only if it sounds correct.</p>
        <textarea value={text} onChange={(e) => setText(e.target.value)} />

        <div className={`voice-validation ${canApprove ? 'ready' : ''}`}>
          <div>
            <span className="section-label">Voice preview</span>
            <strong>{dispatch.audio_status || 'NOT GENERATED'}</strong>
            {dispatch.audio_error ? <p>Audio error: {dispatch.audio_error}</p> : null}
            {!previewMatchesText && audioUrl ? <p>Text changed after preview. Generate a fresh preview before approving.</p> : null}
          </div>
          {audioUrl ? (
            <audio controls src={audioUrl}>
              Your browser does not support audio playback.
            </audio>
          ) : null}
        </div>

        <div className="modal-actions">
          <button className="danger-button" onClick={onReject}>CANCEL REQUEST</button>
          <button onClick={onPreviewAudio} disabled={!text.trim()}>GENERATE VOICE PREVIEW</button>
          <button className="success-button" onClick={onApprove} disabled={!canApprove}>APPROVE AFTER LISTENING</button>
          <button onClick={onClose}>CLOSE</button>
        </div>
      </div>
    </div>
  )
}
