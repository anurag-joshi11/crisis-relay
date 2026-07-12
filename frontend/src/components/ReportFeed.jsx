export default function ReportFeed({ reports = [] }) {
  return (
    <section className="panel report-panel">
      <div className="panel-title-row">
        <div>
          <h2>Live Field Report</h2>
          <p className="panel-subtitle">Latest field signal feeding the command picture.</p>
        </div>
        <span className="signal-pill">Signal</span>
      </div>
      <div className="stack">
        {reports.length ? (
          [...reports].reverse().map((report) => (
            <article key={report.report_id} className="card report-card">
              <div className="card-top">
                <strong>{report.scenario_time}</strong>
                <span>{report.source} - {report.channel}</span>
              </div>
              <p>{report.raw_text}</p>
            </article>
          ))
        ) : (
          <div className="empty-panel-note">
            <strong>No field report ingested yet</strong>
            <p>Awaiting the next field update for this incident.</p>
          </div>
        )}
      </div>
    </section>
  )
}
