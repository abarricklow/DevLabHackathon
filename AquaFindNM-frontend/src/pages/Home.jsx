import { useState } from 'react'
import { getRecommendation } from '../services/api'
import InputForm from '../components/InputForm'
import StrategyResults from '../components/StrategyResults'
import CropTable from '../components/CropTable'
import IncomeChart from '../components/IncomeChart'
import FadeIn from '../components/FadeIn'
import SeverityBanner from '../components/SeverityBanner'

// ─────────────────────────────────────────────────────
// Transforms the rich backend response into the flat
// shape that StrategyResults, IncomeChart, and CropTable
// all expect. This keeps the components untouched.
// ─────────────────────────────────────────────────────
function transformResponse(data) {
  // 1. Build income_preserved from strategy_comparison array
  //    Backend uses: "unlimited" | "limited" | "none"
  //    Frontend expects: "interdistrict" | "intradistrict" | "no_trade"
  const institutionMap = {
    unlimited: 'interdistrict',
    limited:   'intradistrict',
    none:      'no_trade',
  }

  const income_preserved = {}
  let recommended_strategy = 'interdistrict'
  let highestPct = -1

  if (Array.isArray(data.strategy_comparison)) {
    data.strategy_comparison.forEach(s => {
      const frontendKey = institutionMap[s.institution] || s.institution
      income_preserved[frontendKey] = Math.round(s.income_preserved_pct)

      // The best strategy is the one with highest income preserved
      if (s.income_preserved_pct > highestPct) {
        highestPct = s.income_preserved_pct
        recommended_strategy = frontendKey
      }
    })
  }

  // 2. Get shadow price — use the highest shadow price across
  //    all crops from buy_vs_fallow as the headline figure
  let shadow_price = 0
  if (Array.isArray(data.buy_vs_fallow) && data.buy_vs_fallow.length > 0) {
    shadow_price = Math.max(...data.buy_vs_fallow.map(b => b.shadow_price || 0))
  }

  // 3. Build buy water recommendation from headline or buy_vs_fallow
  const buy_crops = Array.isArray(data.buy_vs_fallow)
    ? data.buy_vs_fallow
        .filter(b => b.recommendation === 'buy_water')
        .map(b => b.crop)
    : []

  const buy_water_recommendation = buy_crops.length > 0
    ? `Buying water is economically justified for: ${buy_crops.join(', ')}. ` +
      `Current shadow price: $${shadow_price.toFixed(2)}/acre-ft. ` +
      `${data.headline_recommendation || ''}`
    : data.headline_recommendation ||
      `Under current conditions, fallowing low-value crops is more cost-effective than purchasing water at market rates.`

  // 4. Build crop_adjustments from crop_recommendations
  //    Backend gives recommended_acres and current_acres
  //    Frontend expects acreage_pct (retention fraction)
  const crop_adjustments = Array.isArray(data.crop_recommendations)
    ? data.crop_recommendations.map(r => ({
        crop: r.crop,
        acreage_pct: r.current_acres > 0
          ? Math.min(1, r.recommended_acres / r.current_acres)
          : 0,
      }))
    : []

  return {
    recommended_strategy,
    income_preserved,
    shadow_price: Math.round(shadow_price * 100) / 100,
    buy_water_recommendation,
    crop_adjustments,
    // pass through the raw data too in case you need it later
    _raw: data,
  }
}

export default function Home() {
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [shortage, setShortage] = useState(null)
  const [userCrops, setUserCrops] = useState({})

  const handleSubmit = async (farmData) => {
    setLoading(true)
    setError(null)
    setShortage(farmData.shortage_pct)

    // Build userCrops map for CropTable: { pecan: 500, alfalfa: 200 }
    const cropsMap = {}
    if (Array.isArray(farmData.crops)) {
      farmData.crops.forEach(({ crop, acres }) => {
        cropsMap[crop] = acres
      })
    }
    setUserCrops(cropsMap)

    try {
      const raw = await getRecommendation(farmData)
      console.log('Raw API response:', JSON.stringify(raw, null, 2))

      const transformed = transformResponse(raw)
      console.log('Transformed response:', JSON.stringify(transformed, null, 2))

      setResults(transformed)
    } catch (err) {
      console.error('API error:', err)
      console.error('Response data:', err.response?.data)
      setError('Could not get recommendations. Make sure the backend is running.')
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setResults(null)
    setError(null)
    setShortage(null)
    setUserCrops({})
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--cream)' }}>

      {/* Header */}
      <div
        className="px-8 py-4 flex items-center justify-between"
        style={{ backgroundColor: 'var(--green-2)' }}
      >
        <div className="flex items-center gap-3">
          <span className="text-3xl">🌾</span>
          <div>
            <h1 className="text-xl font-bold leading-tight text-white">
              WaterOptix
            </h1>
            <p className="text-xs" style={{ color: 'var(--green-4)' }}>
              Powered by NMSU Rio Grande Basin Research
            </p>
          </div>
        </div>

        <div
          className="text-xs font-semibold px-4 py-2 rounded-full transition-all"
          style={{
            backgroundColor: results ? 'var(--green-1)' : 'rgba(255,255,255,0.1)',
            color: results ? 'white' : 'var(--green-4)',
          }}
        >
          {results ? '✓ Analysis Complete' : 'Awaiting Input'}
        </div>
      </div>

      {/* Two column layout */}
      <div className="flex h-[calc(100vh-73px)]">

        {/* Left column */}
        <div
          className="w-[420px] shrink-0 overflow-y-auto p-6"
          style={{
            backgroundColor: 'white',
            borderRight: '1px solid var(--cream-2)',
          }}
        >
          <div className="mb-5">
            <p
              className="text-xs font-semibold uppercase tracking-widest mb-1"
              style={{ color: 'var(--green-1)' }}
            >
              Step 1
            </p>
            <h2 className="text-base font-bold" style={{ color: 'var(--text-dark)' }}>
              Enter Your Farm Details
            </h2>
            <p className="text-xs mt-0.5" style={{ color: 'var(--text-light)' }}>
              All fields help improve recommendation accuracy
            </p>
          </div>

          <InputForm onSubmit={handleSubmit} />
        </div>

        {/* Right column */}
        <div className="flex-1 overflow-y-auto p-8">

          {/* Empty state */}
          {!results && !loading && !error && (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="text-6xl mb-4">🌿</div>
              <h2
                className="text-xl font-semibold mb-2"
                style={{ color: 'var(--green-1)' }}
              >
                No results yet
              </h2>
              <p style={{ color: 'var(--text-light)' }} className="max-w-sm text-sm">
                Fill in your farm details on the left and submit to see
                your personalized drought adaptation recommendations.
              </p>
            </div>
          )}

          {/* Loading state */}
          {loading && (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="text-5xl mb-4 animate-bounce">💧</div>
              <p
                className="animate-pulse text-sm"
                style={{ color: 'var(--text-light)' }}
              >
                Calculating recommendations...
              </p>
            </div>
          )}

          {/* Error state */}
          {error && !loading && (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="text-5xl mb-4">⚠️</div>
              <p className="text-sm text-red-500 max-w-sm">{error}</p>
              <button
                onClick={handleReset}
                className="mt-4 text-xs underline"
                style={{ color: 'var(--text-light)' }}
              >
                Try again
              </button>
            </div>
          )}

          {/* Results */}
          {results && !loading && (
            <div className="max-w-2xl">
              <div className="flex items-start justify-between mb-2">
                <SeverityBanner shortage={shortage} />
                <button
                  onClick={handleReset}
                  className="text-xs underline shrink-0 ml-4 mt-1 transition-colors"
                  style={{ color: 'var(--text-light)' }}
                  onMouseOver={e => e.target.style.color = 'var(--green-1)'}
                  onMouseOut={e => e.target.style.color = 'var(--text-light)'}
                >
                  ↺ Start over
                </button>
              </div>

              <FadeIn delay={0}>
                <CropTable results={results} userCrops={userCrops} />
              </FadeIn>
              <FadeIn delay={150}>
                <StrategyResults results={results} />
              </FadeIn>
              <FadeIn delay={300}>
                <IncomeChart results={results} />
              </FadeIn>
            </div>
          )}

        </div>
      </div>
    </div>
  )
}