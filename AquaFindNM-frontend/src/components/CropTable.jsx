import { CheckCircle, XCircle, AlertCircle } from 'lucide-react'
import Tooltip from './Tooltip'

const ACTION_META = {
  maintain: {
    label: 'Maintain',
    icon: <CheckCircle size={16} />,
    colors: 'bg-green-100 text-green-700',
    rowBg: 'bg-white',
  },
  reduce: {
    label: 'Reduce Acreage',
    icon: <AlertCircle size={16} />,
    colors: 'bg-yellow-100 text-yellow-700',
    rowBg: 'bg-yellow-50',
  },
  fallow: {
    label: 'Fallow',
    icon: <XCircle size={16} />,
    colors: 'bg-red-100 text-red-700',
    rowBg: 'bg-red-50',
  },
}

function getAction(acreagePct) {
  if (acreagePct >= 0.85) return 'maintain'
  if (acreagePct > 0) return 'reduce'
  return 'fallow'
}

function AcreageBar({ pct }) {
  const color =
    pct >= 0.85 ? 'bg-green-400' :
    pct > 0 ? 'bg-yellow-400' :
    'bg-red-300'

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-gray-200 rounded-full h-2">
        <div
          className={`h-2 rounded-full transition-all duration-700 ${color}`}
          style={{ width: `${pct * 100}%` }}
        />
      </div>
      <span className="text-xs font-mono text-gray-500 w-10 text-right">
        {pct === 0 ? '0%' : `${Math.round(pct * 100)}%`}
      </span>
    </div>
  )
}

function ActionBadge({ action }) {
  const meta = ACTION_META[action]
  return (
    <span className={`
      inline-flex items-center gap-1 text-xs font-semibold
      px-2 py-0.5 rounded-full ${meta.colors}
    `}>
      {meta.icon}
      {meta.label}
    </span>
  )
}

function CropRow({ crop, acreagePct, userAcres }) {
  const action = getAction(acreagePct)
  const meta = ACTION_META[action]
  const recommendedAcres = userAcres
    ? Math.round(userAcres * acreagePct)
    : null

  return (
    <tr className={`border-t border-gray-100 ${meta.rowBg}`}>
      <td className="py-3 px-4">
        <span className="font-medium text-gray-800 capitalize">{crop}</span>
      </td>
      <td className="py-3 px-4 text-sm text-gray-500 text-right">
        {userAcres ? `${userAcres.toLocaleString()} ac` : '—'}
      </td>
      <td className="py-3 px-4 text-sm text-right">
        {recommendedAcres !== null ? (
          <span className={action === 'fallow' ? 'text-red-500 font-semibold' : 'text-gray-700'}>
            {recommendedAcres === 0 ? 'Fallow' : `${recommendedAcres.toLocaleString()} ac`}
          </span>
        ) : '—'}
      </td>
      <td className="py-3 px-4 min-w-[140px]">
        <AcreageBar pct={acreagePct} />
      </td>
      <td className="py-3 px-4">
        <ActionBadge action={action} />
      </td>
    </tr>
  )
}

function SummaryRow({ cropAdjustments, userCrops }) {
  const totalUserAcres = Object.values(userCrops || {}).reduce((a, b) => a + b, 0)
  const totalRecommended = cropAdjustments.reduce((sum, item) => {
    const userAcres = userCrops?.[item.crop] || 0
    return sum + Math.round(userAcres * item.acreage_pct)
  }, 0)

  const fallowCount = cropAdjustments.filter(c => c.acreage_pct === 0).length
  const maintainCount = cropAdjustments.filter(c => c.acreage_pct >= 0.85).length
  const reduceCount = cropAdjustments.filter(
    c => c.acreage_pct > 0 && c.acreage_pct < 0.85
  ).length

  return (
    <div className="mt-4 grid grid-cols-3 gap-3">
      <div className="rounded-lg bg-green-50 border border-green-200 p-3 text-center">
        <p className="text-2xl font-bold text-green-600">{maintainCount}</p>
        <p className="text-xs text-green-700 mt-0.5">Crops to Maintain</p>
      </div>
      <div className="rounded-lg bg-yellow-50 border border-yellow-200 p-3 text-center">
        <p className="text-2xl font-bold text-yellow-600">{reduceCount}</p>
        <p className="text-xs text-yellow-700 mt-0.5">Crops to Reduce</p>
      </div>
      <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-center">
        <p className="text-2xl font-bold text-red-600">{fallowCount}</p>
        <p className="text-xs text-red-700 mt-0.5">Crops to Fallow</p>
      </div>

      {totalUserAcres > 0 && (
        <div className="col-span-3 rounded-lg bg-blue-50 border border-blue-200 p-3 flex justify-between items-center">
          <span className="text-sm text-blue-700 font-medium">Total Recommended Acreage</span>
          <span className="font-bold text-blue-800">
            {totalRecommended.toLocaleString()} / {totalUserAcres.toLocaleString()} ac
          </span>
        </div>
      )}
    </div>
  )
}

export default function CropTable({ results, userCrops }) {
  if (!results?.crop_adjustments) return null

  const { crop_adjustments } = results
  const sorted = [...crop_adjustments].sort((a, b) => b.acreage_pct - a.acreage_pct)

  return (
    <div className="mt-8">

      {/* Section heading with tooltip */}
      <div className="flex items-center mb-1">
        <h2 className="text-xl font-bold text-gray-800">
          Crop Acreage Adjustments
        </h2>
        <Tooltip text="Shows how many acres of each crop to plant under your shortage scenario. Crops with higher income per acre-foot of water are prioritized." />
      </div>
      <p className="text-sm text-gray-400 mb-4">
        Recommended acreage for each crop under your shortage scenario
      </p>

      <div className="rounded-xl border border-gray-200 overflow-hidden shadow-sm">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">
              <th className="py-3 px-4">Crop</th>
              <th className="py-3 px-4 text-right">Your Acres</th>
              <th className="py-3 px-4 text-right">Recommended</th>

              {/* Retention column with tooltip */}
              <th className="py-3 px-4">
                <div className="flex items-center gap-1">
                  Retention
                  <Tooltip text="The percentage of your normal acreage recommended under this shortage. 100% means no change, 0% means fallow the entire crop." />
                </div>
              </th>

              {/* Action column with tooltip */}
              <th className="py-3 px-4">
                <div className="flex items-center gap-1">
                  Action
                  <Tooltip text="Maintain means keep full acreage. Reduce means plant fewer acres. Fallow means skip this crop entirely this season." />
                </div>
              </th>
            </tr>
          </thead>

          <tbody>
            {sorted.map(item => (
              <CropRow
                key={item.crop}
                crop={item.crop}
                acreagePct={item.acreage_pct}
                userAcres={userCrops?.[item.crop] || null}
              />
            ))}
          </tbody>
        </table>
      </div>

      <SummaryRow cropAdjustments={crop_adjustments} userCrops={userCrops} />
    </div>
  )
}