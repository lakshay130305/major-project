import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './auth.jsx'
import Login from './pages/Login.jsx'
import AdminLayout from './pages/admin/AdminLayout.jsx'
import Dashboard from './pages/admin/Dashboard.jsx'
import TouristSearch from './pages/admin/TouristSearch.jsx'
import Incidents from './pages/admin/Incidents.jsx'
import Analytics from './pages/admin/Analytics.jsx'
import TouristApp from './pages/tourist/TouristApp.jsx'

function Protected({ role, children }) {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  if (role && user.role !== role) return <Navigate to="/" replace />
  return children
}

function Home() {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  return <Navigate to={user.role === 'admin' ? '/admin' : '/app'} replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<Home />} />

      <Route path="/admin" element={<Protected role="admin"><AdminLayout /></Protected>}>
        <Route index element={<Dashboard />} />
        <Route path="tourists" element={<TouristSearch />} />
        <Route path="incidents" element={<Incidents />} />
        <Route path="analytics" element={<Analytics />} />
      </Route>

      <Route path="/app" element={<Protected role="tourist"><TouristApp /></Protected>} />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
