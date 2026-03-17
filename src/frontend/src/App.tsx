import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import IngestionPage from './pages/IngestionPage'
import ManagePage from './pages/ManagePage'
import HistoryPage from './pages/HistoryPage'

const navClass = ({ isActive }: { isActive: boolean }) =>
  isActive ? 'text-blue-600 font-medium' : 'text-gray-600 hover:text-gray-800'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <nav className="bg-white border-b border-gray-200 px-6 py-3 flex items-center gap-6">
          <span className="font-bold text-gray-800 text-lg">SheetManipulator</span>
          <NavLink to="/" end className={navClass}>
            Ingest
          </NavLink>
          <NavLink to="/manage" className={navClass}>
            Manage
          </NavLink>
          <NavLink to="/history" className={navClass}>
            History
          </NavLink>
        </nav>
        <main className="p-6">
          <Routes>
            <Route path="/" element={<IngestionPage />} />
            <Route path="/manage" element={<ManagePage />} />
            <Route path="/history" element={<HistoryPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
