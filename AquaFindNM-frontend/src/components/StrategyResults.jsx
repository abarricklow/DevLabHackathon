import { Trophy, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import Tooltip from './Tooltip'

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
    border: 'var(--green-1)',
    badge: { backgroundColor: 'var(--green-4)', color: 'var(--green-2)' },
    bar: 'var(--green-1)',
    icon: 'var(--green-1)',
  }
  if (rank === 2) return {
    border: '#CA8A04',
    badge: { backgroundColor: '#FEF9C3', color: '#713F12' },
    bar: '#FACC15',
    icon: '#CA8A04',
  }
  return {
    border: '#FCA5A5',
    badge: { backgroundColor: '#FEE2E2', color: '#991B1B' },
    bar: '#FCA5A5',
    icon: '#EF4444',
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
    <div
      className={`relative rounded-2xl border-2 p-5 transition-all ${isRecommended ? 'shadow-lg scale-[1.02]' : 'shadow-sm'}`}
      style={{
        borderColor: colors.border,
        backgroundColor: 'var(--cream)',
      }}
    >
      {/* Recommended badge */}
      {isRecommended && (
        <div
          className="absolute -top-3 left-4 flex items-center gap-1 text-white text-xs font-bold px-3 py-1 rounded-full shadow"
          style={{ backgroundColor: 'var(--green-1)' }}
        >
          <Trophy size={12} />
          Best Option
        </div>
      )}

      {/* Header row */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <span
            className="text-xs font-semibold px-2 py-0.5 rounded-full"
            style={colors.badge}
          >
            #{rank} Strategy
          </span>
          <h3
            className="font-bold mt-1 text-base"
            style={{ color: 'var(--text-dark)' }}
          >
            {meta.label}
          </h3>
        </div>
        <div style={{ color: colors.icon }} className="mt-1">
          {getTrendIcon(rank)}
        </div>
      </div>

      {/* Income preserved bar */}
      <div className="mb-3">
        <div className="flex items-center justify-between text-sm mb-1">
          <div className="flex items-center">
            <span style={{ color: 'var(--text-light)' }}>Income Preserved</span>
            <Tooltip text="The percentage of your total farm income retained under this strategy compared to a full water supply year." />
          </div>
          <span className="font-bold" style={{ color: 'var(--text-dark)' }}>
            {incomePct}%
          </span>
        </div>
        <div className="w-full rounded-full h-2.5" style={{ backgroundColor: 'var(--cream-2)' }}>
          <div
            className="h-2.5 rounded-full transition-all duration-700"
            style={{
              width: `${incomePct}%`,
              backgroundColor: colors.bar,
            }}
          />
        </div>
      </div>

      {/* Description */}
      <p className="text-sm" style={{ color: 'var(--text-mid)' }}>
        {meta.description}
      </p>
    </div>
  )
}

function ShadowPriceCallout({ shadowPrice, buyRecommendation }) {
  return (
    <div
      className="mt-6 rounded-xl p-4"
      style={{
        backgroundColor: 'var(--green-4)',
        border: '1px solid var(--green-1)',
      }}
    >
      <div className="flex items-center mb-1">
        <h4 className="font-semibold" style={{ color: 'var(--green-2)' }}>
          💧 Should You Buy Water?
        </h4>
        <Tooltip text="The shadow price is the maximum you should pay per acre-foot of water before it becomes cheaper to fallow that crop instead." />
      </div>
      <p className="text-sm" style={{ color: 'var(--green-1)' }}>
        {buyRecommendation}
      </p>
      <p className="text-xs mt-1" style={{ color: 'var(--green-1)', opacity: 0.7 }}>
        Shadow price of water:{' '}
        <span className="font-mono font-semibold">${shadowPrice}/acre-ft</span>
      </p>
    </div>
  )
}

export default function StrategyResults({ results }) {
  if (!results) return null

  const { recommended_strategy, income_preserved, shadow_price, buy_water_recommendation } = results

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

      {/* Section heading with tooltip */}
      <div className="flex items-center mb-1">
        <h2 className="text-xl font-bold" style={{ color: 'var(--text-dark)' }}>
          Recommended Strategies
        </h2>
        <Tooltip text="Strategies are ranked by how much farm income is preserved under your shortage level. The best option depends on what trading arrangements are legally available to you." />
      </div>
      <p className="text-sm mb-5" style={{ color: 'var(--text-light)' }}>
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