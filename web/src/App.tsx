import { BrowserRouter, Link, Route, Routes } from 'react-router-dom'
import { api, DEFAULT_CYCLE_ID } from './api'
import CommandCenter from './screens/CommandCenter'
import Home from './screens/Home'

function Details() {
  return (
    <>
      <header className="topbar">
        <span className="wordmark"><span className="mark" /><span>Payroll<b>Pilot</b></span></span>
        <span className="crumb">Pilot Co / <strong>Cycle {DEFAULT_CYCLE_ID}</strong></span>
        <span className="spacer" />
        <Link to="/" className="small">Back to home</Link>
        <span className={`tag ${api.mode === 'fixture' ? 'prov-seeded_issue' : 'prov-real'} prov`}>{api.mode === 'fixture' ? 'Fixture data · synthetic' : 'Live API'}</span>
      </header>
      {api.mode === 'fixture' && (
        <div className="simbar">Fixture simulation: synthetic data, no messages leave this browser, replies are scripted test replies.</div>
      )}
      <main className="page">
        <CommandCenter />
      </main>
    </>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/details" element={<Details />} />
        <Route path="/e/:id" element={<Details />} />
        <Route path="/inbox/:id" element={<Details />} />
        <Route path="*" element={<Home />} />
      </Routes>
    </BrowserRouter>
  )
}
