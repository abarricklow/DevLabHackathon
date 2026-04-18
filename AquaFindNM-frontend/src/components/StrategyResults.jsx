import { Trophy, TrendingUp, TrendingDown, Minus } from 'lucide-react'

const STRATEGY_META = {
  interdistrict: {
    label: 'Full Interdistrict Trading',
    description: 'Buy and sell water across district lines. Highest flexibility — water flows to its highest-value use.',
  },
  intradistrict: {
    label: 'Intradistrict Trading Only',
    description: 'Trade water within your district only. Moderate flexibility with fewer legal hurdles.',
  },
  no_trade: {
    label: 'Proportional Shortage Sharing',
    description: 'Everyone takes the same percentage cut. No trading — simplest to administer but least efficient.',
  },
}

function getColorScheme(rank) {
  if (rank === 1) return {
    border: 'border-green-400',
    bg: 'bg-green-50',
    badge: 'bg-green-100 text-green-700',
    bar: 'bg-green-400',
    icon: 'text-green-500',
  }
  if (rank === 2) return {
    border: 'border-yellow-400',
    bg: 'bg-yellow-50',
    badge: 'bg-yellow-100 text-yellow-700',
    bar: 'bg-yellow-400',
    icon: 'text-yellow-500',
  }
  return {
    border: 'border-red-300',
    bg: 'bg-red-50',
    badge: 'bg-red-100 text-red-700',
    bar: 'bg-red-300',
    icon: 'text-red-400',
  }
}

function getTrendIcon(rank) {
  if (rank === 1) return <TrendingUp size={18} />
  if (rank === 2) return <Minus size={18} />
  return <TrendingDown size={18} />
}

function StrategyCard({ strategy, incomePct, rank, isRecommended }) {
  const meta = STRATEGY_META[strategy]
  const colors = getColorScheme(rank)

  return (
    <div className={`
      relative rounded-xl border-2 p-5 transition-all
      ${colors.border} ${colors.bg}
      ${isRecommended ? 'shadow-lg scale-[1.02]' : 'shadow-sm'}
    `}>

      {/* Recommended badge */}
      {isRecommended && (
        <div className="absolute -top-3 left-4 flex items-center gap-1 bg-green-500 text-white text-xs font-bold px-3 py-1 rounded-full shadow">
          <Trophy size={12} />
          Best Option
        </div>
      )}

      {/* Header row */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${colors.badge}`}>
            #{rank} Strategy
          </span>
          <h3 className="font-bold text-gray-800 mt-1 text-base">{meta.label}</h3>
        </div>
        <div className={`${colors.icon} mt-1`}>
          {getTrendIcon(rank)}
        </div>
      </div>

      {/* Income preserved bar */}
      <div className="mb-3">
        <div className="flex justify-between text-sm mb-1">
          <span className="text-gray-500">Income Preserved</span>
          <span className="font-bold text-gray-800">{incomePct}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div
            className={`h-2.5 rounded-full transition-all duration-700 ${colors.bar}`}
            style={{ width: `${incomePct}%` }}
          />
        </div>
      </div>

      {/* Description */}
      <p className="text-sm text-gray-600">{meta.description}</p>
    </div>
  )
}

function ShadowPriceCallout({ shadowPrice, buyRecommendation }) {
  return (
    <div className="mt-6 rounded-xl border border-blue-200 bg-blue-50 p-4">
      <h4 className="font-semibold text-blue-800 mb-1">💧 Should You Buy Water?</h4>
      <p className="text-sm text-blue-700">{buyRecommendation}</p>
      <p className="text-xs text-blue-400 mt-1">
        Shadow price of water: <span className="font-mono font-semibold">${shadowPrice}/acre-ft</span>
      </p>
    </div>
  )
}

export default function StrategyResults({ results }) {
  if (!results) return null

  const { recommended_strategy, income_preserved, shadow_price, buy_water_recommendation } = results

  // Sort strategies by income preserved, highest first
  const ranked = Object.entries(income_preserved)
    .sort((a, b) => b[1] - a[1])
    .map(([strategy, pct], index) => ({
      strategy,
      incomePct: pct,
      rank: index + 1,
      isRecommended: strategy === recommended_strategy,
    }))

  return (
    <div className="mt-8">
      <h2 className="text-xl font-bold text-gray-800 mb-1">Recommended Strategies</h2>
      <p className="text-sm text-gray-400 mb-5">
        Ranked by income preserved under your shortage scenario
      </p>

      <div className="flex flex-col gap-5">
        {ranked.map(item => (
          <StrategyCard key={item.strategy} {...item} />
        ))}
      </div>

      <ShadowPriceCallout
        shadowPrice={shadow_price}
        buyRecommendation={buy_water_recommendation}
      />
    </div>
  )
}