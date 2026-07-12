const stageCopy = [
  {
    id: 'reports',
    label: '1',
    title: 'Field reports arrive',
    detail: 'Raw wildfire updates move through the scenario feed one report at a time.',
  },
  {
    id: 'engine',
    label: '2',
    title: 'Gemini and state engine interpret',
    detail: 'Reports become state events, active needs, blockers, and unconfirmed operations.',
  },
  {
    id: 'issue',
    label: '3',
    title: 'Command center flags risk',
    detail: 'The operator sees what is unverified and why it matters operationally.',
  },
  {
    id: 'approval',
    label: '4',
    title: 'Voice preview is validated',
    detail: 'The message is generated, listened to, and only then approved by a human.',
  },
  {
    id: 'audit',
    label: '5',
    title: 'Decision is recorded',
    detail: 'The dashboard shows the decision history and Solana receipt status.',
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
        <span className="section-label">Demo flow</span>
        <h2>{scenario.id} / {scenario.name}</h2>
        <p>
          Show the wildfire workflow as one chain: incoming reports, extracted operational state,
          unconfirmed risk, human-validated voice message, then audit history.
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
            <h2>End-to-end path</h2>
            <p className="panel-subtitle">Use this as the judge-facing story before opening the live command view.</p>
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
