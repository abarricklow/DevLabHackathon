import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from 'recharts'

const STRATEGY_LABELS = {
  interdistrict: 'Full Trading',
  intradistrict: 'District Trading',
  no_trade: 'No Trading',
}

const COLORS = {
  interdistrict: '#4ade80',  // green
  intradistrict: '#facc15',  // yellow
  no_trade: '#f87171',       // red
}

// Custom tooltip that appears on hover
function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null

  const { strategy, income_pct } = payload[0].payload

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3 text-sm">
      <p className="font-semibold text-gray-800 mb-1">
        {STRATEGY_LABELS[strategy]}
      </p>
      <p className="text-gray-500">
        Income Preserved:{' '}
        <span className="font-bold text-gray-800">{income_pct}%</span>
      </p>
    </div>
  )
}

// Custom bar label that sits on top of each bar
function CustomBarLabel({ x, y, width, value }) {
  return (
    <text
      x={x + width / 2}
      y={y - 8}
      textAnchor="middle"
      className="fill-gray-600"
      fontSize={13}
      fontWeight={600}
    >
      {value}%
    </text>
  )
}

export default function IncomeChart({ results }) {
  if (!results?.income_preserved) return null

  // Transform the income_preserved object into an array recharts can use
  const data = Object.entries(results.income_preserved)
    .map(([strategy, income_pct]) => ({
      strategy,
      label: STRATEGY_LABELS[strategy],
      income_pct,
      fill: COLORS[strategy],
    }))
    .sort((a, b) => b.income_pct - a.income_pct)

  const recommended = results.recommended_strategy

  return (
    <div className="mt-8">
      <h2 className="text-xl font-bold text-gray-800 mb-1">Income Comparison</h2>
      <p className="text-sm text-gray-400 mb-6">
        Percentage of farm income preserved under each adaptation strategy
      </p>

      {/* Chart */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart
            data={data}
            margin={{ top: 24, right: 16, left: 0, bottom: 8 }}
            barCategoryGap="35%"
          >
            <CartesianGrid
              strokeDasharray="3 3"
              vertical={false}
              stroke="#f0f0f0"
            />

            <XAxis
              dataKey="label"
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 12, fill: '#9ca3af' }}
            />

            <YAxis
              domain={[0, 100]}
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 12, fill: '#9ca3af' }}
              tickFormatter={(v) => `${v}%`}
              width={40}
            />

            {/* Reference line at 70% — the no-trade baseline */}
            <ReferenceLine
              y={70}
              stroke="#e5e7eb"
              strokeDasharray="4 4"
              label={{
                value: 'No-trade baseline',
                position: 'insideTopRight',
                fontSize: 11,
                fill: '#d1d5db',
              }}
            />

            <Tooltip
              content={<CustomTooltip />}
              cursor={{ fill: 'rgba(0,0,0,0.04)' }}
            />

            <Bar
              dataKey="income_pct"
              radius={[6, 6, 0, 0]}
              label={<CustomBarLabel />}
            >
              {data.map((entry) => (
                <Cell
                  key={entry.strategy}
                  fill={entry.fill}
                  opacity={
                    entry.strategy === recommended ? 1 : 0.55
                  }
                />
              ))}
            </Bar>

          </BarChart>
        </ResponsiveContainer>

        {/* Legend */}
        <div className="flex items-center justify-center gap-6 mt-2">
          {data.map((entry) => (
            <div key={entry.strategy} className="flex items-center gap-1.5">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: entry.fill }}
              />
              <span className="text-xs text-gray-500">{entry.label}</span>
              {entry.strategy === recommended && (
                <span className="text-xs font-semibold text-green-600">
                  ★ Best
                </span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Income gap callout */}
      <IncomeGapCallout data={data} recommended={recommended} />
    </div>
  )
}

// Shows the dollar impact difference between best and worst strategy
function IncomeGapCallout({ data, recommended }) {
  const best = data.find(d => d.strategy === recommended)
  const worst = data[data.length - 1]

  if (!best || !worst || best.strategy === worst.strategy) return null

  const gap = best.income_pct - worst.income_pct

  return (
    <div className="mt-4 rounded-xl border border-indigo-200 bg-indigo-50 p-4 flex items-start gap-3">
      <span className="text-2xl">📊</span>
      <div>
        <p className="text-sm font-semibold text-indigo-800">
          {gap} percentage points of income at stake
        </p>
        <p className="text-sm text-indigo-600 mt-0.5">
          Choosing <span className="font-semibold">{STRATEGY_LABELS[best.strategy]}</span> preserves{' '}
          <span className="font-semibold">{gap}% more income</span> than{' '}
          <span className="font-semibold">{STRATEGY_LABELS[worst.strategy]}</span> under your current shortage scenario.
        </p>
      </div>
    </div>
  )
}