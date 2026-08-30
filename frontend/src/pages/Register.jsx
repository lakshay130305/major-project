import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import api from '../api'
import { useAuth } from '../auth.jsx'

const emptyContact = { name: '', phone: '', relation: 'family' }
const emptyStop = { name: '', lat: '', lng: '' }

export default function Register() {
  const { login } = useAuth()
  const nav = useNavigate()
  const [f, setF] = useState({
    full_name: '', nationality: 'Indian', document_type: 'aadhaar',
    document_number: '', phone: '', email: '', password: '',
    trip_start: '', trip_end: '',
  })
  const [contacts, setContacts] = useState([{ ...emptyContact }])
  const [stops, setStops] = useState([{ ...emptyStop }])
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const set = (k) => (e) => setF({ ...f, [k]: e.target.value })

  const REQUIRED_FIELDS = [
    ['full_name', 'Full name'],
    ['document_number', 'Document number'],
    ['phone', 'Phone'],
    ['trip_start', 'Trip start'],
    ['trip_end', 'Trip end'],
    ['email', 'Email'],
    ['password', 'Password'],
  ]

  // Client-side validation is a UX convenience, not the security boundary --
  // the backend's own TouristCreate schema (required fields, email format,
  // password strength, trip_end > trip_start) still rejects an invalid
  // payload sent straight to the API. This just catches it before the round
  // trip and gives a plain-language message instead of a raw 422.
  const validate = () => {
    const missing = REQUIRED_FIELDS.filter(([k]) => !f[k].trim()).map(([, label]) => label)
    if (missing.length) return `Please fill in: ${missing.join(', ')}.`
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(f.email)) return 'Enter a valid email address.'
    if (f.password.length < 8 || !/[A-Za-z]/.test(f.password) || !/\d/.test(f.password)) {
      return 'Password must be at least 8 characters and contain both letters and numbers.'
    }
    if (new Date(f.trip_end) <= new Date(f.trip_start)) return 'Trip end must be after trip start.'
    return ''
  }

  const submit = async (e) => {
    e.preventDefault()
    const validationError = validate()
    if (validationError) {
      setError(validationError)
      return
    }
    setError('')
    setLoading(true)
    try {
      const payload = {
        full_name: f.full_name,
        nationality: f.nationality,
        document_type: f.document_type,
        document_number: f.document_number,
        phone: f.phone,
        email: f.email,
        password: f.password,
        trip_start: new Date(f.trip_start).toISOString(),
        trip_end: new Date(f.trip_end).toISOString(),
        emergency_contacts: contacts.filter((c) => c.name && c.phone),
        itinerary: stops
          .filter((s) => s.name && s.lat && s.lng)
          .map((s) => ({ name: s.name, lat: Number(s.lat), lng: Number(s.lng) })),
      }
      const { data } = await api.post('/tourists', payload)
      setResult(data)
      setTimeout(async () => {
        const u = await login(f.email, f.password)
        nav(u.role === 'admin' ? '/admin' : '/app')
      }, 1500)
    } catch (err) {
      const d = err.response?.data?.detail
      setError(typeof d === 'string' ? d : (Array.isArray(d) ? d.map((x) => x.msg).join('; ') : 'Registration failed'))
    } finally {
      setLoading(false)
    }
  }

  if (result) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-100 p-4">
        <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-8 text-center">
          <div className="text-5xl mb-3">✅</div>
          <h1 className="text-xl font-bold">Digital Tourist ID Issued</h1>
          <div className="mt-3 text-2xl font-mono font-bold text-sky-700">{result.digital_id}</div>
          <p className="text-sm text-slate-500 mt-2">
            Valid until {new Date(result.trip_end).toLocaleDateString()}. Signing you in…
          </p>
        </div>
      </div>
    )
  }

  const input = 'mt-1 w-full border border-slate-300 rounded-lg px-3 py-2 text-slate-900 placeholder:text-slate-400 focus:ring-2 focus:ring-sky-500 outline-none'

  return (
    <div className="min-h-screen bg-slate-100 py-8 px-4">
      <div className="max-w-2xl mx-auto bg-white rounded-2xl shadow-xl p-6 sm:p-8">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-xl font-bold">🧳 Tourist Registration (KYC)</h1>
          <Link to="/login" className="text-sm text-sky-600">Back to login</Link>
        </div>

        <form onSubmit={submit} className="space-y-5">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <label className="text-sm font-medium text-slate-600">Full name
              <input className={input} value={f.full_name} onChange={set('full_name')} required minLength={2} /></label>
            <label className="text-sm font-medium text-slate-600">Nationality
              <input className={input} value={f.nationality} onChange={set('nationality')} /></label>
            <label className="text-sm font-medium text-slate-600">Document type
              <select className={input} value={f.document_type} onChange={set('document_type')}>
                <option value="aadhaar">Aadhaar</option>
                <option value="passport">Passport</option>
                <option value="voterid">Voter ID</option>
                <option value="pan">PAN</option>
              </select></label>
            <label className="text-sm font-medium text-slate-600">Document number
              <input className={input} value={f.document_number} onChange={set('document_number')} required minLength={4} /></label>
            <label className="text-sm font-medium text-slate-600">Phone
              <input className={input} value={f.phone} onChange={set('phone')} required /></label>
            <div />
            <label className="text-sm font-medium text-slate-600">Trip start
              <input type="datetime-local" className={input} value={f.trip_start} onChange={set('trip_start')} required /></label>
            <label className="text-sm font-medium text-slate-600">Trip end
              <input type="datetime-local" className={input} value={f.trip_end} onChange={set('trip_end')} required /></label>
          </div>

          <fieldset className="border border-slate-200 rounded-xl p-4">
            <legend className="text-sm font-semibold px-2">Emergency Contacts</legend>
            {contacts.map((c, i) => (
              <div key={i} className="grid grid-cols-3 gap-2 mb-2">
                <input placeholder="Name" className={input} value={c.name}
                  onChange={(e) => setContacts(contacts.map((x, j) => j === i ? { ...x, name: e.target.value } : x))} />
                <input placeholder="Phone" className={input} value={c.phone}
                  onChange={(e) => setContacts(contacts.map((x, j) => j === i ? { ...x, phone: e.target.value } : x))} />
                <input placeholder="Relation" className={input} value={c.relation}
                  onChange={(e) => setContacts(contacts.map((x, j) => j === i ? { ...x, relation: e.target.value } : x))} />
              </div>
            ))}
            <button type="button" className="text-xs text-sky-600" onClick={() => setContacts([...contacts, { ...emptyContact }])}>+ add contact</button>
          </fieldset>

          <fieldset className="border border-slate-200 rounded-xl p-4">
            <legend className="text-sm font-semibold px-2">Itinerary (waypoints)</legend>
            {stops.map((s, i) => (
              <div key={i} className="grid grid-cols-3 gap-2 mb-2">
                <input placeholder="Place name" className={input} value={s.name}
                  onChange={(e) => setStops(stops.map((x, j) => j === i ? { ...x, name: e.target.value } : x))} />
                <input placeholder="Latitude" type="number" step="any" className={input} value={s.lat}
                  onChange={(e) => setStops(stops.map((x, j) => j === i ? { ...x, lat: e.target.value } : x))} />
                <input placeholder="Longitude" type="number" step="any" className={input} value={s.lng}
                  onChange={(e) => setStops(stops.map((x, j) => j === i ? { ...x, lng: e.target.value } : x))} />
              </div>
            ))}
            <button type="button" className="text-xs text-sky-600" onClick={() => setStops([...stops, { ...emptyStop }])}>+ add waypoint</button>
          </fieldset>

          <fieldset className="border border-slate-200 rounded-xl p-4">
            <legend className="text-sm font-semibold px-2">Login (required — to access the tourist app)</legend>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <label className="text-sm font-medium text-slate-600">Email
                <input type="email" className={input} value={f.email} onChange={set('email')} required /></label>
              <label className="text-sm font-medium text-slate-600">Password (min 8, letters + numbers)
                <input type="password" className={input} value={f.password} onChange={set('password')} required minLength={8} /></label>
            </div>
          </fieldset>

          {error && <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-2">{error}</div>}

          <button disabled={loading}
            className="w-full bg-sky-600 hover:bg-sky-700 text-white font-semibold py-2.5 rounded-lg disabled:opacity-60">
            {loading ? 'Issuing digital ID…' : 'Register & Issue Digital ID'}
          </button>
        </form>
      </div>
    </div>
  )
}
