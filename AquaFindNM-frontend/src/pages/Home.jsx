import { useState } from 'react'
import InputForm from '../components/InputForm'
import StrategyResults from '../components/StrategyResults'
import CropTable from '../components/CropTable'
import IncomeChart from '../components/IncomeChart'
import FadeIn from '../components/FadeIn'
import SeverityBanner from '../components/SeverityBanner'

export default function Home() {
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [userCrops, setUserCrops] = useState({})
  const [shortage, setShortage] = useState(null)   // ← new

  const handleSubmit = async (farmData) => {
    setLoading(true)
    setUserCrops(farmData.crops)
    setShortage(farmData.shortage)                 // ← new
    try {
      const data = {
        recommended_strategy: "interdistrict",
        income_preserved: {
          interdistrict: 92,
          intradistrict: 87,
          no_trade: 70
        },
        shadow_price: 58.14,
        buy_water_recommendation:
          "Buying water is worth it if you can source it under $58/acre-ft. Above that price, fallowing your lowest-value crops is the cheaper option.",
        crop_adjustments: [
          { crop: "pecan",   acreage_pct: 0.878 },
          { crop: "alfalfa", acreage_pct: 0.617 },
          { crop: "corn",    acreage_pct: 0.582 },
          { crop: "wheat",   acreage_pct: 0.000 },
          { crop: "peppers", acreage_pct: 0.924 },
          { crop: "cotton",  acreage_pct: 0.464 },
          { crop: "onions",  acreage_pct: 0.977 },
          { crop: "beans",   acreage_pct: 0.609 },
        ]
      }

      // const data = await getRecommendation(farmData)
      setResults(data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  // ← new: reset handler used by the Start Over button
  const handleReset = () => {
    setResults(null)
    setUserCrops({})
    setShortage(null)
  }

  return (
    <div className="min-h-screen bg-gray-50">

      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-8 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-3xl">🌾</span>
          <div>
            <h1 className="text-xl font-bold text-gray-800 leading-tight">
              Drought Adaptation Advisor
            </h1>
          </div>
        </div>

        {/* Status pill */}
        <div className={`
          text-xs font-semibold px-3 py-1.5 rounded-full
          ${results
            ? 'bg-green-100 text-green-700'
            : 'bg-gray-100 text-gray-400'
          }
        `}>
          {results ? '✓ Analysis Complete' : 'Awaiting Input'}
        </div>
      </div>

      {/* Two column layout */}
      <div className="flex h-[calc(100vh-73px)]">

        {/* ---- LEFT COLUMN ---- */}
        <div className="w-[420px] shrink-0 border-r border-gray-200 bg-white overflow-y-auto p-6">

          {/* Suggestion 6 — form section label */}
          <div className="mb-5">
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-1">
              Step 1
            </p>
            <h2 className="text-base font-bold text-gray-700">Enter Your Farm Details</h2>
            <p className="text-xs text-gray-400 mt-0.5">
              All fields help improve recommendation accuracy
            </p>
          </div>

          <InputForm onSubmit={handleSubmit} />
        </div>

        {/* ---- RIGHT COLUMN ---- */}
        <div className="flex-1 overflow-y-auto p-8">

          {/* Empty state */}
          {!results && !loading && (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="text-6xl mb-4">🌾</div>
              <h2 className="text-xl font-semibold text-gray-600 mb-2">
                No results yet
              </h2>
              <p className="text-gray-400 max-w-sm">
                Fill in your farm details on the left and submit to see
                your personalized drought adaptation recommendations.
              </p>
            </div>
          )}

          {/* Loading state */}
          {loading && (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="text-5xl mb-4 animate-bounce">💧</div>
              <p className="text-gray-400 animate-pulse">
                Calculating recommendations...
              </p>
            </div>
          )}

          {/* Results */}
          {results && !loading && (
            <div className="max-w-2xl">

              {/* Suggestion 5 — severity banner + reset button sit together at the top */}
              <div className="flex items-start justify-between mb-2">
                <SeverityBanner shortage={shortage} />
                <button
                  onClick={handleReset}
                  className="text-xs text-gray-400 hover:text-gray-600 underline shrink-0 ml-4 mt-1"
                >
                  ↺ Start over
                </button>
              </div>

              <FadeIn delay={0}>
                <StrategyResults results={results} />
              </FadeIn>
              <FadeIn delay={150}>
                <IncomeChart results={results} />
              </FadeIn>
              <FadeIn delay={300}>
                <CropTable results={results} userCrops={userCrops} />
              </FadeIn>

            </div>
          )}

        </div>
      </div>
    </div>
  )
}