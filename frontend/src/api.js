import dashboardSnapshot from './mocks/dashboard.json'
import dispatchResult from './mocks/dispatch_result.json'
import { MOCK_AUDIO_DATA_URI } from './audioUrl'

const API_BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/+$/, '')
const USE_MOCKS = (import.meta.env.VITE_USE_MOCKS || 'false') === 'true'
const USE_REAL_APPROVALS = (import.meta.env.VITE_REAL_APPROVALS || 'false') === 'true'
let mockSnapshot = structuredClone(dashboardSnapshot)

function friendlyError(detail) {
  const known = {
    blindspot_not_found: 'That active issue is no longer available. Try the latest issue.',
    dispatch_not_found: 'That update request is no longer available.',
    operation_not_found: 'The related operation could not be found.',
  }
  return known[detail] || detail.replaceAll('_', ' ')
}

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  })
  if (!res.ok) {
    let detail = ''
    try {
      const body = await res.json()
      detail = body.detail ? `:${friendlyError(String(body.detail))}` : ''
    } catch {
      detail = ''
    }
    throw new Error(`request_failed:${res.status}${detail}`)
  }
  return res.json()
}

export async function getDashboard() {
  if (USE_MOCKS) return structuredClone(mockSnapshot)
  return request('/api/demo/status')
}

export async function resetDemo() {
  if (USE_MOCKS) {
    mockSnapshot = structuredClone(dashboardSnapshot)
    return structuredClone(mockSnapshot)
  }
  return request('/api/demo/reset', { method: 'POST' })
}

export async function nextEvent() {
  if (USE_MOCKS) {
    mockSnapshot = {
      ...structuredClone(mockSnapshot),
      reports: [
        ...mockSnapshot.reports,
        {
          report_id: 'RPT-025',
          scenario_time: '10:54',
          source: 'SCOUT_4',
          channel: 'SATELLITE_TEXT',
          raw_text: 'No visual confirmation of Tanker Two drop completion. Smoke column still building east of Sector Four.',
        },
      ],
      scenario: {
        ...mockSnapshot.scenario,
        current_time: '10:54',
      },
      blindspots: mockSnapshot.blindspots.map((blindspot) => (
        blindspot.blindspot_id === 'BS-001'
          ? {
              ...blindspot,
              minutes_in_state: 41,
              reason: "Water-drop fulfilment remains unverified. Tanker 2's latest confirmed state is still DISPATCHED.",
            }
          : blindspot
      )),
      selected_timeline: {
        ...mockSnapshot.selected_timeline,
        related_active_need: {
          scenario_time: '10:54',
          evidence: 'No visual confirmation of Tanker Two drop completion. Smoke column still building east of Sector Four.',
        },
      },
      demo: {
        ...mockSnapshot.demo,
        event_index: 25,
      },
    }
    return structuredClone(mockSnapshot)
  }
  return request('/api/demo/next-event', { method: 'POST' })
}

export async function draftStatusRequest(blindspotId) {
  if (USE_REAL_APPROVALS) return request(`/api/blindspots/${blindspotId}/draft-status-request`, { method: 'POST' })
  if (USE_MOCKS) return { ...structuredClone(dispatchResult), blindspot_id: blindspotId }
  return request(`/api/blindspots/${blindspotId}/draft-status-request`, { method: 'POST' })
}

export async function approveDispatch(dispatchId, approvedText) {
  if (USE_REAL_APPROVALS) {
    return request(`/api/dispatches/${dispatchId}/approve`, {
      method: 'POST',
      body: JSON.stringify({ approved_text: approvedText }),
    })
  }
  if (USE_MOCKS) {
    return {
      ...dispatchResult,
      dispatch_id: dispatchId,
      approved_text: approvedText,
      approval_status: 'APPROVED',
      approval_id: 'MOCK-APR-001',
      approved_at: new Date().toISOString(),
      payload_hash: 'mock-hash-not-submitted-on-chain',
      solana_status: 'PENDING_SYNC',
      solana_signature: null,
      audio_url: null,
    }
  }
  return request(`/api/dispatches/${dispatchId}/approve`, {
    method: 'POST',
    body: JSON.stringify({ approved_text: approvedText }),
  })
}

export async function previewDispatchAudio(dispatchId, approvedText) {
  if (USE_REAL_APPROVALS) {
    return request(`/api/dispatches/${dispatchId}/preview-audio`, {
      method: 'POST',
      body: JSON.stringify({ approved_text: approvedText }),
    })
  }
  if (USE_MOCKS) {
    return {
      ...dispatchResult,
      dispatch_id: dispatchId,
      approved_text: approvedText,
      approval_status: 'PENDING',
      audio_status: 'AVAILABLE',
      audio_url: MOCK_AUDIO_DATA_URI,
      audio_preview_text: approvedText,
      solana_status: 'NOT_SUBMITTED',
    }
  }
  return request(`/api/dispatches/${dispatchId}/preview-audio`, {
    method: 'POST',
    body: JSON.stringify({ approved_text: approvedText }),
  })
}

export async function rejectDispatch(dispatchId) {
  if (USE_REAL_APPROVALS) return request(`/api/dispatches/${dispatchId}/reject`, { method: 'POST' })
  if (USE_MOCKS) {
    return { ...structuredClone(dispatchResult), dispatch_id: dispatchId, approval_status: 'REJECTED' }
  }
  return request(`/api/dispatches/${dispatchId}/reject`, { method: 'POST' })
}

export async function getOperationTimeline(operationId) {
  if (USE_MOCKS) return { ...structuredClone(mockSnapshot.selected_timeline), operation_id: operationId }
  return request(`/api/operations/${operationId}/timeline`)
}
