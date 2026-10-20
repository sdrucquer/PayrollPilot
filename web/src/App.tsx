import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { api, DEFAULT_CYCLE_ID } from './api'
import CommandCenter from './screens/CommandCenter'

export default function App() {
  return (
    <BrowserRouter>
      <header className="topbar">
        <span className="wordmark"><span className="mark" /><span>Payroll<b>Pilot</b></span></span>
        <span className="crumb">Pilot Co / <strong>Cycle {DEFAULT_CYCLE_ID}</strong></span>
        <span className="spacer" />
        <span className={`tag ${api.mode === 'fixture' ? 'prov-seeded_issue' : 'prov-real'} prov`}>{api.mode === 'fixture' ? 'Fixture data · synthetic' : 'Live API'}</span>
      </header>
      {api.mode === 'fixture' && (
        <div className="simbar">Fixture simulation: synthetic data, no messages leave this browser, replies are scripted test replies.</div>
      )}
      <main className="page">
        <Routes>
          <Route path="/" element={<CommandCenter />} />
          <Route path="/e/:id" element={<CommandCenter />} />
          <Route path="/inbox" element={<CommandCenter />} />
          <Route path="/inbox/:id" element={<CommandCenter />} />
          <Route path="*" element={<CommandCenter />} />
        </Routes>
      </main>
    </BrowserRouter>
  )
}
