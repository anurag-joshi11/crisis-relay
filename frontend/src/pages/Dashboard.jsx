import React, { useEffect, useState } from 'react'
import { approveDispatch, draftStatusRequest, getDashboard, getOperationTimeline, nextEvent, rejectDispatch, resetDemo } from '../api'
import Header from '../components/Header'
import ReportFeed from '../components/ReportFeed'
import OperationPanel from '../components/OperationPanel'
import UnconfirmedPanel from '../components/UnconfirmedPanel'
import CommandIntelligence from '../components/CommandIntelligence'
import ApprovalModal from '../components/ApprovalModal'
import AudioPlayer from '../components/AudioPlayer'
import DecisionHistory from '../components/DecisionHistory'

export default function Dashboard() {
  const [snapshot, setSnapshot] = useState(null)
  const [selectedBlindspot, setSelectedBlindspot] = useState(null)
  const [dispatchDraft, setDispatchDraft] = useState(null)
  const [approvalText, setApprovalText] = useState('')
  const [error, setError] = useState('')
  const [processing, setProcessing] = useState(false)
  const [timeline, setTimeline] = useState(null)
  const [approvalOpen, setApprovalOpen] = useState(false)
  const [decisionsByBlindspot, setDecisionsByBlindspot] = useState({})

  useEffect(() => {
    getDashboard().then((data) => {
      setSnapshot(data)
      setSelectedBlindspot(data.blindspots?.[0] || null)
    }).catch((e) => setError(e.message))
  }, [])

  useEffect(() => {
    if (!selectedBlindspot) return
    getOperationTimeline(selectedBlindspot.operation_id).then(setTimeline).catch((e) => setError(e.message))
  }, [selectedBlindspot, snapshot?.demo?.event_index])

  async function handleReset() {
    setProcessing(true)
    try {
      const data = await resetDemo()
      setSnapshot(data)
      setSelectedBlindspot(data.blindspots?.[0] || null)
      setDispatchDraft(null)
      setApprovalOpen(false)
      setDecisionsByBlindspot({})
    } finally {
      setProcessing(false)
    }
  }

  async function handleNext() {
    setProcessing(true)
    try {
      const data = await nextEvent()
      setSnapshot(data)
      setSelectedBlindspot((current) => (
        data.blindspots?.find((blindspot) => blindspot.blindspot_id === current?.blindspot_id)
        || data.blindspots?.[0]
        || null
      ))
    } finally {
      setProcessing(false)
    }
  }

  async function handleDraft() {
    if (!selectedBlindspot) return
    const data = await draftStatusRequest(selectedBlindspot.blindspot_id)
    setDispatchDraft(data)
    setApprovalText(data.ai_draft || '')
    setApprovalOpen(true)
  }

  async function handleApprove() {
    if (!dispatchDraft) return
    const data = await approveDispatch(dispatchDraft.dispatch_id, approvalText)
    setDispatchDraft(data)
    recordDecision('APPROVED', 'Resource update requested. Awaiting field confirmation.')
    setApprovalOpen(false)
  }

  async function handleReject() {
    if (!dispatchDraft) return
    const data = await rejectDispatch(dispatchDraft.dispatch_id)
    setDispatchDraft(data)
    recordDecision('REJECTED', 'Request cancelled. Nothing was broadcast.')
    setApprovalOpen(false)
  }

  function recordDecision(status, summary) {
    if (!selectedBlindspot) return
    const decision = {
      status,
      summary,
      time: snapshot?.scenario?.current_time || '--:--',
      blindspot_id: selectedBlindspot.blindspot_id,
      operation_id: selectedBlindspot.operation_id,
      resource_id: selectedBlindspot.resource_id,
    }
    setDecisionsByBlindspot((current) => ({
      ...current,
      [selectedBlindspot.blindspot_id]: [decision, ...(current[selectedBlindspot.blindspot_id] || [])],
    }))
  }

  if (!snapshot) return <div className="shell">Loading...</div>

  return (
    <div className="shell">
      <Header scenario={snapshot.scenario} onReset={handleReset} onNext={handleNext} processing={processing} />
      {error ? <div className="error">{error}</div> : null}
      <main className="console-grid">
        <aside className="left-rail">
          <ReportFeed reports={snapshot.reports} />
          <UnconfirmedPanel
            blindspots={snapshot.blindspots}
            selectedBlindspot={selectedBlindspot}
            decisionsByBlindspot={decisionsByBlindspot}
            onSelect={setSelectedBlindspot}
          />
          <OperationPanel operations={snapshot.operations} />
          <DecisionHistory
            blindspot={selectedBlindspot}
            decisions={selectedBlindspot ? decisionsByBlindspot[selectedBlindspot.blindspot_id] || [] : []}
          />
        </aside>

        <section className="mission-focus">
          <CommandIntelligence
            blindspot={selectedBlindspot}
            timeline={timeline}
            dispatch={dispatchDraft}
            decision={selectedBlindspot ? decisionsByBlindspot[selectedBlindspot.blindspot_id]?.[0] : null}
            onDraft={handleDraft}
          />
        </section>
      </main>
      {dispatchDraft ? <AudioPlayer audioUrl={dispatchDraft.audio_url} /> : null}
      {dispatchDraft && approvalOpen ? (
        <>
          <ApprovalModal
            dispatch={dispatchDraft}
            text={approvalText}
            setText={setApprovalText}
            onReject={handleReject}
            onApprove={handleApprove}
            onClose={() => setApprovalOpen(false)}
          />
        </>
      ) : null}
    </div>
  )
}
