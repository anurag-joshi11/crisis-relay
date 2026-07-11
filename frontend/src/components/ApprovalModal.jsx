export default function ApprovalModal({ dispatch, text, setText, onReject, onApprove, onClose }) {
  if (!dispatch) return null
  return (
    <div className="modal-backdrop">
      <div className="modal">
        <h3>Approval</h3>
        <textarea value={text} onChange={(e) => setText(e.target.value)} />
        <div className="modal-actions">
          <button onClick={onReject}>REJECT</button>
          <button onClick={onApprove}>APPROVE & BROADCAST</button>
          <button onClick={onClose}>CLOSE</button>
        </div>
      </div>
    </div>
  )
}

