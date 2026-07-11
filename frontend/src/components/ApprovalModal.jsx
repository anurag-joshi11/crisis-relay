export default function ApprovalModal({ dispatch, text, setText, onReject, onApprove, onClose }) {
  if (!dispatch) return null
  return (
    <div className="modal-backdrop">
      <div className="modal">
        <div className="card-top">
          <h3>Review Resource Update</h3>
          <span>{dispatch.dispatch_id}</span>
        </div>
        <p className="muted">Edit the exact message. Nothing is broadcast unless you approve it.</p>
        <textarea value={text} onChange={(e) => setText(e.target.value)} />
        <div className="modal-actions">
          <button className="danger-button" onClick={onReject}>CANCEL REQUEST</button>
          <button className="success-button" onClick={onApprove} disabled={!text.trim()}>APPROVE UPDATE</button>
          <button onClick={onClose}>CLOSE</button>
        </div>
      </div>
    </div>
  )
}
