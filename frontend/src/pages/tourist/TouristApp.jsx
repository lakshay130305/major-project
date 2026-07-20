import { useEffect, useRef, useState } from 'react'
import { MapContainer, TileLayer, Marker, Polygon, Circle } from 'react-leaflet'
import { useNavigate } from 'react-router-dom'
import api from '../../api'
import { useAuth } from '../../auth.jsx'
import { ScoreGauge, Card } from '../../components/ui.jsx'
import { touristIcon, policeIcon, riskColor } from '../../components/mapIcons'
import { haversineKm } from '../../components/geo'

export default function TouristApp() {
  const { user, logout } = useAuth()
  const nav = useNavigate()
  const tid = user.tourist_id
  const [me, setMe] = useState(null)
  const [score, setScore] = useState(null)
  const [zones, setZones] = useState([])
  const [units, setUnits] = useState([])
  const [tracking, setTracking] = useState(true)
  const [toast, setToast] = useState(null)
  const [sosSent, setSosSent] = useState(null)
  const posRef = useRef(null)

  const load = async () => {
    const [m, s, z, u] = await Promise.all([
      api.get(`/tourists/${tid}`),
      api.get(`/tourists/${tid}/safety-score`),
      api.get('/zones'),
      api.get('/police-units'),
    ])
    setMe(m.data); setScore(s.data); setZones(z.data); setUnits(u.data)
    setTracking(m.data.tracking_enabled)
    posRef.current = [m.data.last_lat, m.data.last_lng]
  }
  useEffect(() => { load() }, [])

  // Opt-in live tracking: periodically nudge position and push to backend pipeline.
  useEffect(() => {
    if (!tracking || !me) return
    const iv = setInterval(async () => {
      const [lat, lng] = posRef.current
      const nlat = lat + (Math.random() - 0.5) * 0.002
      const nlng = lng + (Math.random() - 0.5) * 0.002
      posRef.current = [nlat, nlng]
      const { data } = await api.post(`/tourists/${tid}/location`, { lat: nlat, lng: nlng, speed_kmh: 5 })
      setScore((s) => ({ ...s, score: data.safety_score, band: data.band }))
      setMe((m) => ({ ...m, last_lat: nlat, last_lng: nlng, safety_score: data.safety_score }))
      if (data.alerts_raised?.length) {
        setToast(`⚠ ${data.alerts_raised.join(', ').replace(/_/g, ' ')}`)
        setTimeout(() => setToast(null), 4000)
      }
    }, 5000)
    return () => clearInterval(iv)
  }, [tracking, me?.id])

  const toggleTracking = async () => {
    const next = !tracking
    setTracking(next)
    await api.post(`/tourists/${tid}/tracking?enabled=${next}`)
  }

  const sendSOS = async () => {
    const [lat, lng] = posRef.current
    const { data } = await api.post(`/tourists/${tid}/sos`, { lat, lng, message: 'Emergency! Need help.' })
    setSosSent(data)
    load()
  }

  if (!me || !score) return <div className="p-6 text-center text-slate-500">Loading…</div>

  const inZones = zones.filter((z) => pointInPoly(me.last_lat, me.last_lng, z.polygon))
  const riskyZone = inZones.find((z) => ['high', 'restricted'].includes(z.risk_level))
  const nearby = [...units]
    .map((u) => ({ ...u, dist: haversineKm(me.last_lat, me.last_lng, u.lat, u.lng) }))
    .sort((a, b) => a.dist - b.dist).slice(0, 3)

  const nextStop = me.itinerary?.[0]

  return (
    <div className="min-h-screen bg-slate-100 pb-24">
      <header className="bg-sky-600 text-white px-4 py-3 flex items-center justify-between sticky top-0 z-[1000]">
        <div>
          <div className="text-xs opacity-80">Digital Tourist ID</div>
          <div className="font-bold">{me.digital_id}</div>
        </div>
        <button onClick={() => { logout(); nav('/login') }} className="text-sm bg-sky-700 px-3 py-1 rounded-lg">Logout</button>
      </header>

      {toast && (
        <div className="fixed top-16 left-1/2 -translate-x-1/2 bg-orange-500 text-white px-4 py-2 rounded-lg shadow-lg z-[1001] text-sm">
          {toast}
        </div>
      )}

      <div className="max-w-md mx-auto p-4 space-y-4">
        {/* safety score */}
        <div className="bg-white rounded-xl shadow-sm p-4 flex items-center gap-4">
          <ScoreGauge score={score.score} />
          <div>
            <div className="text-sm text-slate-500">My Safety Score</div>
            <div className="text-lg font-bold">{me.full_name}</div>
            <div className="text-xs text-slate-500 mt-1">
              Zone: {score.breakdown.zone}<br />
              {score.breakdown.night_penalty ? '🌙 Night-time caution' : '☀️ Daytime'}
            </div>
          </div>
        </div>

        {/* geofence warning */}
        {riskyZone ? (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4">
            <div className="font-semibold text-red-700">⚠ Geo-fence Warning</div>
            <div className="text-sm text-red-600 mt-1">
              You are in <b>{riskyZone.name}</b> ({riskyZone.risk_level} risk). Stay alert and consider leaving the area.
            </div>
          </div>
        ) : (
          <div className="bg-green-50 border border-green-200 rounded-xl p-3 text-sm text-green-700">
            ✅ You are in a safe area.
          </div>
        )}

        {/* map */}
        <div className="bg-white rounded-xl shadow-sm overflow-hidden" style={{ height: 240 }}>
          <MapContainer center={[me.last_lat, me.last_lng]} zoom={14} style={{ height: '100%' }} key={me.id}>
            <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution="&copy; OSM" />
            {zones.map((z) => (
              <Polygon key={z.id} positions={z.polygon}
                pathOptions={{ color: riskColor[z.risk_level], fillOpacity: 0.15, weight: 1.5 }} />
            ))}
            <Marker position={[me.last_lat, me.last_lng]} icon={touristIcon(score.score)} />
            {nearby.map((u) => <Marker key={u.id} position={[u.lat, u.lng]} icon={policeIcon} />)}
          </MapContainer>
        </div>

        {/* live tracking toggle */}
        <div className="bg-white rounded-xl shadow-sm p-4 flex items-center justify-between">
          <div>
            <div className="font-medium">Live Location Tracking</div>
            <div className="text-xs text-slate-500">Opt-in — lets the control room protect you</div>
          </div>
          <button onClick={toggleTracking}
            className={`w-14 h-8 rounded-full transition relative ${tracking ? 'bg-green-500' : 'bg-slate-300'}`}>
            <span className={`absolute top-1 w-6 h-6 bg-white rounded-full transition-all ${tracking ? 'left-7' : 'left-1'}`}></span>
          </button>
        </div>

        {/* itinerary tracker */}
        <Card title="Itinerary Tracker">
          <ol className="space-y-2">
            {me.itinerary?.map((w, i) => (
              <li key={i} className="flex items-center gap-2 text-sm">
                <span className={`w-2.5 h-2.5 rounded-full ${i === 0 ? 'bg-sky-500' : 'bg-slate-300'}`}></span>
                <span className={i === 0 ? 'font-medium' : 'text-slate-500'}>{w.name}</span>
                {i === 0 && <span className="text-xs text-sky-600 ml-auto">next stop</span>}
              </li>
            ))}
          </ol>
        </Card>

        {/* nearby police */}
        <Card title="Nearby Police Stations">
          <ul className="space-y-2">
            {nearby.map((u) => (
              <li key={u.id} className="flex items-center justify-between text-sm">
                <div>
                  <div className="font-medium">{u.name}</div>
                  <div className="text-xs text-slate-500">{u.station} · ☎ {u.phone}</div>
                </div>
                <span className="text-xs text-slate-500">{u.dist.toFixed(1)} km</span>
              </li>
            ))}
          </ul>
        </Card>

        {sosSent && (
          <div className="bg-red-600 text-white rounded-xl p-4 text-sm">
            <div className="font-bold">🚨 SOS Sent</div>
            {sosSent.nearest_unit && (
              <div className="mt-1">Dispatched <b>{sosSent.nearest_unit.name}</b> ({sosSent.nearest_unit.station}) — {sosSent.nearest_unit.distance_km} km away.</div>
            )}
            <div className="mt-1 text-red-100 text-xs">Emergency contacts notified: {sosSent.notified_contacts?.map((c) => c.name).join(', ')}</div>
          </div>
        )}
      </div>

      {/* SOS button */}
      <div className="fixed bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-slate-100 to-transparent">
        <div className="max-w-md mx-auto">
          <button onClick={sendSOS}
            className="w-full bg-red-600 hover:bg-red-700 text-white font-bold text-lg py-4 rounded-2xl shadow-lg sos-pulse">
            🆘 SOS — Send Emergency Alert
          </button>
        </div>
      </div>
    </div>
  )
}

// Point-in-polygon (ray casting) for [[lat,lng],...] rings.
function pointInPoly(lat, lng, poly) {
  if (!poly || poly.length < 3) return false
  let inside = false
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [yi, xi] = poly[i], [yj, xj] = poly[j]
    const intersect = (xi > lng) !== (xj > lng) &&
      lat < ((yj - yi) * (lng - xi)) / (xj - xi) + yi
    if (intersect) inside = !inside
  }
  return inside
}
