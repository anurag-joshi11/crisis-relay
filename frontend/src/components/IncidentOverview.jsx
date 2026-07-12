const stageCopy = [
  {
    id: 'reports',
    label: '1',
    title: 'Field reports received',
    detail: 'Incoming wildfire updates are added to the incident record as they arrive.',
  },
  {
    id: 'engine',
    label: '2',
    title: 'Operational state updated',
    detail: 'Reports are converted into state events, active needs, blockers, and resource status.',
  },
  {
    id: 'issue',
    label: '3',
    title: 'Risk requiring action',
    detail: 'Unconfirmed operations are elevated when the latest confirmed state is no longer enough.',
  },
  {
    id: 'approval',
    label: '4',
    title: 'Voice message validated',
    detail: 'Outbound status requests are previewed and approved by an operator before use.',
  },
  {
    id: 'audit',
    label: '5',
    title: 'Decision recorded',
    detail: 'Approved and cancelled actions are retained in the operational audit log.',
  },
]

function stageState(stageId, { reportCount, openIssues, decisionsCount, dispatch }) {
  if (stageId === 'reports') return reportCount > 0 ? 'live' : 'ready'
  if (stageId === 'engine') return reportCount > 0 ? 'live' : 'ready'
  if (stageId === 'issue') return openIssues > 0 ? 'critical' : 'ready'
  if (stageId === 'approval') return dispatch?.audio_status === 'AVAILABLE' ? 'live' : 'ready'
  if (stageId === 'audit') return decisionsCount > 0 ? 'live' : 'ready'
  return 'ready'
}

function stateLabel(state) {
  if (state === 'critical') return 'Needs action'
  if (state === 'live') return 'Active'
  return 'Ready'
}

export default function IncidentOverview({
  scenario,
  openIssues,
  decisionsCount,
  reportCount,
  eventIndex,
  totalEvents,
  dispatch,
  onOpenCommand,
}) {
  const context = { reportCount, openIssues, decisionsCount, dispatch }

  return (
    <main className="overview-page">
      <section className="panel overview-hero">
        <span className="section-label">Operational flow</span>
        <h2>{scenario.id} / {scenario.name}</h2>
        <p>
          Live incident reports feed resource state, surface unconfirmed operational risk,
          and route outbound status requests through human validation.
        </p>
        <div className="overview-metrics">
          <div>
            <span>Reports processed</span>
            <strong>{eventIndex || reportCount}/{totalEvents || '--'}</strong>
          </div>
          <div>
            <span>Open issues</span>
            <strong>{openIssues}</strong>
          </div>
          <div>
            <span>Recorded decisions</span>
            <strong>{decisionsCount}</strong>
          </div>
        </div>
      </section>

      <section className="panel demo-runway">
        <div className="panel-title-row">
          <div>
            <h2>Incident response path</h2>
            <p className="panel-subtitle">Current status across report intake, resource state, command action, and audit.</p>
          </div>
          <button onClick={onOpenCommand}>Open Command Center</button>
        </div>
        <div className="demo-stage-grid">
          {stageCopy.map((stage) => {
            const state = stageState(stage.id, context)
            return (
              <article key={stage.id} className={`demo-stage stage-${state}`}>
                <div className="demo-stage-marker">{stage.label}</div>
                <div>
                  <div className="demo-stage-top">
                    <h3>{stage.title}</h3>
                    <span>{stateLabel(state)}</span>
                  </div>
                  <p>{stage.detail}</p>
                </div>
              </article>
            )
          })}
        </div>
      </section>
    </main>
  )
}
