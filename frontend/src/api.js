import dashboardSnapshot from './mocks/dashboard.json'
import dispatchResult from './mocks/dispatch_result.json'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const USE_MOCKS = (import.meta.env.VITE_USE_MOCKS || 'true') === 'true'

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  })
  if (!res.ok) {
    throw new Error(`request_failed:${res.status}`)
  }
  return res.json()
}

export async function getDashboard() {
  if (USE_MOCKS) return dashboardSnapshot
  return request('/api/demo/status')
}

export async function resetDemo() {
  if (USE_MOCKS) return dashboardSnapshot
  return request('/api/demo/reset', { method: 'POST' })
}

export async function nextEvent() {
  if (USE_MOCKS) return dashboardSnapshot
  return request('/api/demo/next-event', { method: 'POST' })
}

export async function draftStatusRequest(blindspotId) {
  if (USE_MOCKS) return dispatchResult
  return request(`/api/blindspots/${blindspotId}/draft-status-request`, { method: 'POST' })
}

export async function approveDispatch(dispatchId, approvedText) {
  if (USE_MOCKS) {
    return {
      ...dispatchResult,
      approved_text: approvedText,
      approval_status: 'APPROVED',
      approved_at: new Date().toISOString(),
      solana_status: 'PENDING_SYNC',
    }
  }
  return request(`/api/dispatches/${dispatchId}/approve`, {
    method: 'POST',
    body: JSON.stringify({ approved_text: approvedText }),
  })
}

export async function rejectDispatch(dispatchId) {
  if (USE_MOCKS) {
    return { ...dispatchResult, approval_status: 'REJECTED' }
  }
  return request(`/api/dispatches/${dispatchId}/reject`, { method: 'POST' })
}

export async function getOperationTimeline(operationId) {
  if (USE_MOCKS) return dashboardSnapshot.selected_timeline
  return request(`/api/operations/${operationId}/timeline`)
}
