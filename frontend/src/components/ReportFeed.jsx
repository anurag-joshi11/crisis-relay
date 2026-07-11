export default function ReportFeed({ reports = [] }) {
  return (
    <section className="panel">
      <h2>Incoming Reports</h2>
      <div className="stack">
        {[...reports].reverse().map((report) => (
          <article key={report.report_id} className="card">
            <div className="card-top">
              <strong>{report.scenario_time}</strong>
              <span>{report.source} · {report.channel}</span>
            </div>
            <p>{report.raw_text}</p>
          </article>
        ))}
      </div>
    </section>
  )
}

