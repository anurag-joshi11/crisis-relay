import React, { useEffect, useState } from 'react'
import { approveDispatch, draftStatusRequest, getDashboard, getOperationTimeline, nextEvent, rejectDispatch, resetDemo } from '../api'
import Header from '../components/Header'
import ReportFeed from '../components/ReportFeed'
import OperationPanel from '../components/OperationPanel'
import UnconfirmedPanel from '../components/UnconfirmedPanel'
import CommandIntelligence from '../components/CommandIntelligence'
import ApprovalModal from '../components/ApprovalModal'
import AudioPlayer from '../components/AudioPlayer'

export default function Dashboard() {
  const [snapshot, setSnapshot] = useState(null)
  const [selectedBlindspot, setSelectedBlindspot] = useState(null)
  const [dispatchDraft, setDispatchDraft] = useState(null)
  const [approvalText, setApprovalText] = useState('')
  const [error, setError] = useState('')
  const [processing, setProcessing] = useState(false)
  const [timeline, setTimeline] = useState(null)

  useEffect(() => {
    getDashboard().then((data) => {
      setSnapshot(data)
      setSelectedBlindspot(data.blindspots?.[0] || null)
    }).catch((e) => setError(e.message))
  }, [])

  useEffect(() => {
    if (!selectedBlindspot) return
    getOperationTimeline(selectedBlindspot.operation_id).then(setTimeline).catch((e) => setError(e.message))
  }, [selectedBlindspot])

  async function handleReset() {
    setProcessing(true)
    try {
      const data = await resetDemo()
      setSnapshot(data)
      setSelectedBlindspot(data.blindspots?.[0] || null)
    } finally {
      setProcessing(false)
    }
  }

  async function handleNext() {
    setProcessing(true)
    try {
      const data = await nextEvent()
      setSnapshot(data)
      setSelectedBlindspot(data.blindspots?.[0] || null)
    } finally {
      setProcessing(false)
    }
  }

  async function handleDraft() {
    if (!selectedBlindspot) return
    const data = await draftStatusRequest(selectedBlindspot.blindspot_id)
    setDispatchDraft(data)
    setApprovalText(data.ai_draft || '')
  }

  async function handleApprove() {
    if (!dispatchDraft) return
    const data = await approveDispatch(dispatchDraft.dispatch_id, approvalText)
    setDispatchDraft(data)
  }

  async function handleReject() {
    if (!dispatchDraft) return
    const data = await rejectDispatch(dispatchDraft.dispatch_id)
    setDispatchDraft(data)
  }

  if (!snapshot) return <div className="shell">Loading...</div>

  return (
    <div className="shell">
      <Header scenario={snapshot.scenario} onReset={handleReset} onNext={handleNext} processing={processing} />
      {error ? <div className="error">{error}</div> : null}
      <main className="dashboard-grid">
        <ReportFeed reports={snapshot.reports} />
        <OperationPanel operations={snapshot.operations} />
        <UnconfirmedPanel blindspots={snapshot.blindspots} selectedBlindspot={selectedBlindspot} onSelect={setSelectedBlindspot} />
      </main>
      <CommandIntelligence blindspot={selectedBlindspot} timeline={timeline} dispatch={dispatchDraft} onDraft={handleDraft} />
      {dispatchDraft ? (
        <>
          <AudioPlayer audioUrl={dispatchDraft.audio_url} />
          <ApprovalModal
            dispatch={dispatchDraft}
            text={approvalText}
            setText={setApprovalText}
            onReject={handleReject}
            onApprove={handleApprove}
            onClose={() => setDispatchDraft(null)}
          />
        </>
      ) : null}
    </div>
  )
}
