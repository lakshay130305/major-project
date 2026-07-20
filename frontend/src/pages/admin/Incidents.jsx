import { useEffect, useState } from 'react'
import api from '../../api'
import useWebSocket from '../../useWebSocket'
import { SeverityBadge, StatusBadge, Card } from '../../components/ui.jsx'

const NEXT = { detected: 'acknowledged', acknowledged: 'dispatched', dispatched: 'resolved' }

export default function Incidents() {
  const [incidents, setIncidents] = useState([])
  const [filter, setFilter] = useState('')

  const load = () => {
    const url = filter ? `/incidents?status=${filter}` : '/incidents'
    api.get(url).then((r) => setIncidents(r.data))
  }
  useEffect(load, [filter])
  useWebSocket((ev) => { if (ev.event === 'incident') load() })

  const advance = async (inc) => {
    const next = NEXT[inc.status]
    if (!next) return
    await api.patch(`/incidents/${inc.id}`, { status: next, note: `Advanced to ${next} by operator` })
    load()
  }

  const fmt = (s) => s == null ? '—' : `${Math.round(s)}s`

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-slate-800">Incident Response Workflow</h2>
        <select value={filter} onChange={(e) => setFilter(e.target.value)}
          className="border border-slate-300 rounded-lg px-3 py-1.5 text-sm">
          <option value="">All statuses</option>
          <option value="detected">Detected</option>
          <option value="acknowledged">Acknowledged</option>
          <option value="dispatched">Dispatched</option>
          <option value="resolved">Resolved</option>
        </select>
      </div>

      <div className="space-y-3">
        {incidents.length === 0 && <Card><div className="text-slate-400 text-sm">No incidents.</div></Card>}
        {incidents.map((inc) => (
          <div key={inc.id} className="bg-white rounded-xl shadow-sm p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className="font-semibold">#{inc.id}</span>
                <span className="capitalize">{inc.type.replace('_', ' ')}</span>
                <SeverityBadge severity={inc.severity} />
                <StatusBadge status={inc.status} />
              </div>
              <div className="flex items-center gap-2">
                {NEXT[inc.status] && (
                  <button onClick={() => advance(inc)}
                    className="bg-sky-600 hover:bg-sky-700 text-white text-xs font-semibold px-3 py-1.5 rounded-lg">
                    → {NEXT[inc.status]}
                  </button>
                )}
              </div>
            </div>
            <div className="text-sm text-slate-600 mt-1">{inc.description}</div>
            <div className="flex flex-wrap gap-x-6 gap-y-1 mt-2 text-xs text-slate-500">
              <span>Detected: {new Date(inc.detected_at).toLocaleString()}</span>
              <span>Response time: {fmt(inc.response_time_seconds)}</span>
              {inc.lat && <span>Loc: {inc.lat.toFixed(4)}, {inc.lng.toFixed(4)}</span>}
            </div>
            {/* lifecycle progress */}
            <div className="flex items-center gap-1 mt-3">
              {['detected', 'acknowledged', 'dispatched', 'resolved'].map((s, i) => {
                const order = ['detected', 'acknowledged', 'dispatched', 'resolved']
                const done = order.indexOf(inc.status) >= i
                return (
                  <div key={s} className="flex-1 flex items-center">
                    <div className={`h-1.5 flex-1 rounded ${done ? 'bg-sky-500' : 'bg-slate-200'}`}></div>
                  </div>
                )
              })}
            </div>
            <div className="flex justify-between text-[10px] text-slate-400 mt-1">
              <span>Detected</span><span>Ack</span><span>Dispatched</span><span>Resolved</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
