export default function Header({ scenario, onReset, onNext, processing }) {
  return (
    <header className="header">
      <div className="brand-lockup">
        <div className="brand-row">
          <span className="brand-mark">CR</span>
          <span className="app-title">CrisisRelay</span>
          <span className="system-online">System online</span>
        </div>
        <h1>{scenario.id} / {scenario.name}</h1>
      </div>
      <div className="header-meta">
        <span className="incident-pill">Wildfire response</span>
        <span className="live-pill">LIVE</span>
        <span className="time-readout">{scenario.current_time}</span>
        <button onClick={onReset}>RESET DEMO</button>
        <button onClick={onNext} disabled={processing}>NEXT FIELD REPORT</button>
      </div>
    </header>
  )
}
