export default function SeverityBanner({ shortage }) {
  if (!shortage) return null

  const getSeverity = (pct) => {
    if (pct <= 10) return {
      label: 'Mild Shortage',
      style: {
        backgroundColor: 'var(--green-4)',
        border: '1px solid var(--green-1)',
        color: 'var(--green-2)',
      }
    }
    if (pct <= 25) return {
      label: 'Moderate Shortage',
      style: {
        backgroundColor: '#FEF9C3',
        border: '1px solid #CA8A04',
        color: '#713F12',
      }
    }
    if (pct <= 40) return {
      label: 'Severe Shortage',
      style: {
        backgroundColor: '#FEF3C7',
        border: '1px solid #D97706',
        color: '#92400E',
      }
    }
    return {
      label: 'Critical Shortage',
      style: {
        backgroundColor: '#FEE2E2',
        border: '1px solid #DC2626',
        color: '#991B1B',
      }
    }
  }

  const severity = getSeverity(shortage)

  return (
    <div
      className="rounded-xl px-4 py-3 mb-6 flex items-center gap-3"
      style={severity.style}
    >
      <span className="text-xl">{severity.icon}</span>
      <div>
        <p className="font-semibold text-sm">
          {severity.label} — {shortage}% below normal
        </p>
        <p className="text-xs opacity-75 mt-0.5">
          Recommendations below are calibrated to this shortage level
        </p>
      </div>
    </div>
  )
}