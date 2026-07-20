// Small shared presentational helpers used across both dashboards.

export function bandColor(score) {
  if (score >= 75) return '#16a34a'   // safe - green
  if (score >= 50) return '#eab308'   // moderate - amber
  if (score >= 25) return '#f97316'   // risky - orange
  return '#dc2626'                    // danger - red
}

export function bandLabel(score) {
  if (score >= 75) return 'Safe'
  if (score >= 50) return 'Moderate'
  if (score >= 25) return 'Risky'
  return 'Danger'
}

const SEV = {
  low: 'bg-slate-100 text-slate-700',
  medium: 'bg-yellow-100 text-yellow-800',
  high: 'bg-orange-100 text-orange-800',
  critical: 'bg-red-100 text-red-800',
}

export function SeverityBadge({ severity }) {
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${SEV[severity] || SEV.medium}`}>
      {severity}
    </span>
  )
}

export function StatusBadge({ status }) {
  const map = {
    active: 'bg-green-100 text-green-800',
    sos: 'bg-red-100 text-red-800 sos-pulse',
    missing: 'bg-purple-100 text-purple-800',
    detected: 'bg-red-100 text-red-800',
    acknowledged: 'bg-yellow-100 text-yellow-800',
    dispatched: 'bg-blue-100 text-blue-800',
    resolved: 'bg-green-100 text-green-800',
  }
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${map[status] || 'bg-slate-100 text-slate-700'}`}>
      {status}
    </span>
  )
}

export function ScoreGauge({ score, size = 120 }) {
  const r = size / 2 - 10
  const c = 2 * Math.PI * r
  const pct = Math.max(0, Math.min(100, score)) / 100
  const color = bandColor(score)
  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width={size} height={size}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#e2e8f0" strokeWidth="10" />
        <circle
          cx={size / 2} cy={size / 2} r={r} fill="none" stroke={color} strokeWidth="10"
          strokeDasharray={c} strokeDashoffset={c * (1 - pct)} strokeLinecap="round"
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          style={{ transition: 'stroke-dashoffset .6s ease, stroke .6s ease' }}
        />
      </svg>
      <div className="absolute text-center">
        <div className="text-2xl font-bold" style={{ color }}>{Math.round(score)}</div>
        <div className="text-xs text-slate-500">{bandLabel(score)}</div>
      </div>
    </div>
  )
}

export function Stat({ label, value, accent = 'text-slate-900' }) {
  return (
    <div className="bg-white rounded-xl shadow-sm p-4">
      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
      <div className={`text-2xl font-bold mt-1 ${accent}`}>{value}</div>
    </div>
  )
}

export function Card({ title, children, actions }) {
  return (
    <div className="bg-white rounded-xl shadow-sm">
      {title && (
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
          <h3 className="font-semibold text-slate-800">{title}</h3>
          {actions}
        </div>
      )}
      <div className="p-4">{children}</div>
    </div>
  )
}
