export default function Header({ scenario, onReset, onNext, processing }) {
  return (
    <header className="header">
      <div>
        <div className="eyebrow">CRISISRELAY</div>
        <h1>{scenario.name}</h1>
      </div>
      <div className="header-meta">
        <span className="live-pill">LIVE</span>
        <span>{scenario.current_time}</span>
        <button onClick={onReset}>RESET DEMO</button>
        <button onClick={onNext} disabled={processing}>NEXT FIELD REPORT</button>
      </div>
    </header>
  )
}

