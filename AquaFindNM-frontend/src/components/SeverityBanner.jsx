// src/components/SeverityBanner.jsx
export default function SeverityBanner({ shortage }) {
  if (!shortage) return null

  const getSeverity = (pct) => {
    if (pct <= 10) return { label: 'Mild Shortage', color: 'bg-green-50 border-green-200 text-green-700', icon: '🟢' }
    if (pct <= 25) return { label: 'Moderate Shortage', color: 'bg-yellow-50 border-yellow-200 text-yellow-700', icon: '🟡' }
    if (pct <= 40) return { label: 'Severe Shortage', color: 'bg-orange-50 border-orange-200 text-orange-700', icon: '🟠' }
    return { label: 'Critical Shortage', color: 'bg-red-50 border-red-200 text-red-700', icon: '🔴' }
  }

  const severity = getSeverity(shortage)

  return (
    <div className={`rounded-xl border px-4 py-3 mb-6 flex items-center gap-3 ${severity.color}`}>
      <span className="text-xl">{severity.icon}</span>
      <div>
        <p className="font-semibold text-sm">{severity.label} — {shortage}% below normal</p>
        <p className="text-xs opacity-75 mt-0.5">
          Recommendations below are calibrated to this shortage level
        </p>
      </div>
    </div>
  )
}