import { BrowserRouter, NavLink, Route, Routes } from 'react-router-dom'
import { api } from './api'
import Board from './screens/Board'

function Placeholder({ name }: { name: string }) {
  return <p className="muted">{name} screen arrives in a later task.</p>
}

export default function App() {
  return (
    <BrowserRouter>
      <header className="topbar">
        <h1>PayrollPilot</h1>
        <nav>
          <NavLink to="/" end>Command Center</NavLink>
          <NavLink to="/inbox">Inbox</NavLink>
          <NavLink to="/activity">Activity</NavLink>
          <NavLink to="/review">Review</NavLink>
        </nav>
        <span className={`tag mode-${api.mode}`}>{api.mode === 'fixture' ? 'Fixture data (synthetic)' : 'Live API'}</span>
      </header>
      <main className="page">
        <Routes>
          <Route path="/" element={<Board />} />
          <Route path="/inbox/*" element={<Placeholder name="Inbox" />} />
          <Route path="/activity" element={<Placeholder name="Activity" />} />
          <Route path="/review" element={<Placeholder name="Review" />} />
        </Routes>
      </main>
    </BrowserRouter>
  )
}
