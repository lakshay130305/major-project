import { useEffect, useMemo, useState } from 'react'
import { MapContainer, TileLayer, Polyline, CircleMarker, Marker } from 'react-leaflet'
import { touristIcon } from './mapIcons'

// Time-scrub playback over a tourist's GPS ping history. `pings` is expected
// oldest-first (matches GET /tourists/{id}/pings, which already reverses the
// API's newest-first order for this reason).
export default function TrailReplay({ pings }) {
  const [step, setStep] = useState(pings.length - 1)

  // `pings` arrives empty on first render (the parent clears it while the
  // fetch is in flight) and is replaced in place once it resolves -- this
  // component is never remounted between tourists, so `step` has to be
  // re-synced to "latest" whenever a new ping history lands, instead of
  // only being set once at mount.
  useEffect(() => {
    setStep(pings.length - 1)
  }, [pings])

  // Clamp defensively so a stale `step` from the previous tourist can never
  // index past the end of a shorter `pings` array in the same render pass
  // the effect above hasn't caught up to yet.
  const safeStep = Math.min(Math.max(step, 0), pings.length - 1)
  // Hooks must run unconditionally on every render (the empty-pings early
  // return below happens after them), so these stay useMemo calls rather
  // than moving past the guard.
  const visible = useMemo(() => pings.slice(0, safeStep + 1), [pings, safeStep])
  const path = useMemo(() => visible.map((p) => [p.lat, p.lng]), [visible])
  const current = visible[visible.length - 1]

  if (pings.length === 0) {
    return <div className="text-sm text-slate-400">No location history recorded yet.</div>
  }

  return (
    <div className="space-y-3">
      <div className="rounded-lg overflow-hidden" style={{ height: 260 }}>
        <MapContainer center={[current.lat, current.lng]} zoom={14} style={{ height: '100%' }}>
          <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution="&copy; OSM" />
          <Polyline positions={path} pathOptions={{ color: '#0284c7', weight: 3 }} />
          {visible.map((p, i) => p.is_anomaly && (
            <CircleMarker key={i} center={[p.lat, p.lng]} radius={5}
              pathOptions={{ color: '#dc2626', fillColor: '#dc2626', fillOpacity: 0.9 }} />
          ))}
          <Marker position={[current.lat, current.lng]} icon={touristIcon(100)} />
        </MapContainer>
      </div>

      <div className="flex items-center gap-3">
        <button onClick={() => setStep(0)}
          className="text-xs px-2 py-1 rounded-lg bg-slate-100 hover:bg-slate-200">⏮ Start</button>
        <input type="range" min={0} max={pings.length - 1} value={safeStep}
          onChange={(e) => setStep(Number(e.target.value))}
          className="flex-1" />
        <button onClick={() => setStep(pings.length - 1)}
          className="text-xs px-2 py-1 rounded-lg bg-slate-100 hover:bg-slate-200">Latest ⏭</button>
      </div>

      <div className="flex items-center justify-between text-xs text-slate-500">
        <span>{new Date(current.timestamp).toLocaleString()}</span>
        <span>
          Ping {safeStep + 1} / {pings.length}
          {current.is_anomaly && <span className="ml-2 text-red-600 font-semibold">⚠ anomaly</span>}
        </span>
        <span>{current.speed_kmh?.toFixed(1)} km/h</span>
      </div>
    </div>
  )
}
