import React, { useEffect, useState } from 'react'
import { approveDispatch, draftStatusRequest, getDashboard, getOperationTimeline, nextEvent, previewDispatchAudio, rejectDispatch, resetDemo } from '../api'
import Header from '../components/Header'
import ReportFeed from '../components/ReportFeed'
import OperationPanel from '../components/OperationPanel'
import UnconfirmedPanel from '../components/UnconfirmedPanel'
import CommandIntelligence from '../components/CommandIntelligence'
import ApprovalModal from '../components/ApprovalModal'
import WorkflowNav from '../components/WorkflowNav'
import IncidentOverview from '../components/IncidentOverview'
import DecisionHistoryPage from '../components/DecisionHistoryPage'

export default function Dashboard() {
  const [snapshot, setSnapshot] = useState(null)
  const [selectedBlindspot, setSelectedBlindspot] = useState(null)
  const [dispatchesByBlindspot, setDispatchesByBlindspot] = useState({})
  const [approvalText, setApprovalText] = useState('')
  const [error, setError] = useState('')
  const [processing, setProcessing] = useState(false)
  const [timeline, setTimeline] = useState(null)
  const [approvalOpen, setApprovalOpen] = useState(false)
  const [decisionsByBlindspot, setDecisionsByBlindspot] = useState({})
  const [activeView, setActiveView] = useState('command')

  useEffect(() => {
    getDashboard().then((data) => {
      setSnapshot(data)
      setSelectedBlindspot(data.blindspots?.[0] || null)
      setTimeline(data.selected_timeline || null)
    }).catch((e) => setError(e.message))
  }, [])

  useEffect(() => {
    if (!selectedBlindspot?.operation_id) {
      setTimeline(snapshot?.selected_timeline || null)
      return
    }
    getOperationTimeline(selectedBlindspot.operation_id)
      .then((data) => setTimeline(data))
      .catch((e) => setError(e.message))
  }, [selectedBlindspot?.operation_id, snapshot?.demo?.event_index])

  async function handleReset() {
    setProcessing(true)
    try {
      const data = await resetDemo()
      setSnapshot(data)
      setSelectedBlindspot(data.blindspots?.[0] || null)
      setTimeline(data.selected_timeline || null)
      setDispatchesByBlindspot({})
      setApprovalOpen(false)
      setApprovalText('')
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
    try {
      setError('')
      const data = await draftStatusRequest(selectedBlindspot.blindspot_id)
      setDispatchesByBlindspot((current) => ({
        ...current,
        [selectedBlindspot.blindspot_id]: data,
      }))
      setApprovalText(data.ai_draft || '')
      setApprovalOpen(true)
    } catch (e) {
      setError(e.message)
    }
  }

  async function handleApprove() {
    if (!currentDispatch) return
    try {
      setError('')
      const data = await approveDispatch(currentDispatch.dispatch_id, approvalText)
      setDispatchesByBlindspot((current) => ({
        ...current,
        [selectedBlindspot.blindspot_id]: data,
      }))
      recordDecision('APPROVED', 'Resource update requested. Awaiting field confirmation.')
      setApprovalOpen(false)
    } catch (e) {
      setError(e.message)
    }
  }

  async function handlePreviewAudio() {
    if (!currentDispatch) return
    try {
      setError('')
      const data = await previewDispatchAudio(currentDispatch.dispatch_id, approvalText)
      setDispatchesByBlindspot((current) => ({
        ...current,
        [selectedBlindspot.blindspot_id]: data,
      }))
    } catch (e) {
      setError(e.message)
    }
  }

  async function handleReject() {
    if (!currentDispatch) return
    try {
      setError('')
      const data = await rejectDispatch(currentDispatch.dispatch_id)
      setDispatchesByBlindspot((current) => ({
        ...current,
        [selectedBlindspot.blindspot_id]: data,
      }))
      recordDecision('REJECTED', 'Request cancelled. Nothing was broadcast.')
      setApprovalOpen(false)
    } catch (e) {
      setError(e.message)
    }
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

  const currentDispatch = selectedBlindspot ? dispatchesByBlindspot[selectedBlindspot.blindspot_id] || null : null
  const currentDecisions = selectedBlindspot ? decisionsByBlindspot[selectedBlindspot.blindspot_id] || [] : []
  const allDecisions = Object.values(decisionsByBlindspot).flat()
  const openIssueCount = snapshot.blindspots.filter((blindspot) => !decisionsByBlindspot[blindspot.blindspot_id]?.length).length

  return (
    <div className="shell">
      <Header scenario={snapshot.scenario} onReset={handleReset} onNext={handleNext} processing={processing} />
      <WorkflowNav activeView={activeView} onChange={setActiveView} />
      {error ? <div className="error">{error}</div> : null}
      {activeView === 'overview' ? (
        <IncidentOverview
          scenario={snapshot.scenario}
          openIssues={openIssueCount}
          decisionsCount={allDecisions.length}
          reportCount={snapshot.reports.length}
          eventIndex={snapshot.demo?.event_index}
          totalEvents={snapshot.demo?.total_events}
          dispatch={currentDispatch}
          onOpenCommand={() => setActiveView('command')}
        />
      ) : null}
      {activeView === 'command' ? (
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
          </aside>

          <section className="mission-focus">
            <CommandIntelligence
              blindspot={selectedBlindspot}
              timeline={timeline}
              dispatch={currentDispatch}
              decision={currentDecisions[0]}
              onDraft={handleDraft}
            />
          </section>
        </main>
      ) : null}
      {activeView === 'history' ? (
        <DecisionHistoryPage
          scenario={snapshot.scenario}
          decisions={allDecisions}
          onOpenCommand={() => setActiveView('command')}
        />
      ) : null}
      {currentDispatch && approvalOpen ? (
        <>
          <ApprovalModal
            dispatch={currentDispatch}
            text={approvalText}
            setText={setApprovalText}
            onReject={handleReject}
            onApprove={handleApprove}
            onPreviewAudio={handlePreviewAudio}
            onClose={() => setApprovalOpen(false)}
          />
        </>
      ) : null}
    </div>
  )
}
