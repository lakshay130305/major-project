import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth.jsx'

const DEMO = [
  { label: 'Police / Admin', email: 'admin@tourism.gov.in', password: 'admin123' },
  { label: 'Tourist (Aarav)', email: 'aarav@example.com', password: 'tourist123' },
]

export default function Login() {
  const { login } = useAuth()
  const nav = useNavigate()
  const [email, setEmail] = useState('admin@tourism.gov.in')
  const [password, setPassword] = useState('admin123')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const u = await login(email, password)
      nav(u.role === 'admin' ? '/admin' : '/app')
    } catch (err) {
      setError('Invalid credentials. Try a demo account below.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-sky-600 to-indigo-700 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-8">
        <div className="text-center mb-6">
          <div className="text-4xl mb-2">🛡️</div>
          <h1 className="text-xl font-bold text-slate-800">Smart Tourist Safety</h1>
          <p className="text-sm text-slate-500">Monitoring &amp; Incident Response System</p>
        </div>

        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="text-sm font-medium text-slate-600">Email</label>
            <input value={email} onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full border border-slate-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-sky-500 outline-none"
              type="email" required />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-600">Password</label>
            <input value={password} onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full border border-slate-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-sky-500 outline-none"
              type="password" required />
          </div>
          {error && <div className="text-sm text-red-600">{error}</div>}
          <button disabled={loading}
            className="w-full bg-sky-600 hover:bg-sky-700 text-white font-semibold py-2 rounded-lg transition disabled:opacity-60">
            {loading ? 'Signing in…' : 'Sign In'}
          </button>
        </form>

        <div className="mt-6 border-t border-slate-100 pt-4">
          <p className="text-xs text-slate-400 mb-2">Quick demo login:</p>
          <div className="flex gap-2">
            {DEMO.map((d) => (
              <button key={d.email}
                onClick={() => { setEmail(d.email); setPassword(d.password) }}
                className="flex-1 text-xs border border-slate-200 rounded-lg py-2 hover:bg-slate-50">
                {d.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
