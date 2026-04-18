import { useState } from 'react'
import InputForm from '../components/InputForm'
import StrategyResults from '../components/StrategyResults'
import CropTable from '../components/CropTable'

export default function Home() {
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [userCrops, setUserCrops] = useState({})

  const handleSubmit = async (farmData) => {
    setLoading(true)
    setUserCrops(farmData.crops)
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

  return (
    <div className="min-h-screen bg-gray-50">

      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-8 py-4">
        <h1 className="text-2xl font-bold text-gray-800">Drought Adaptation Advisor</h1>
        <p className="text-sm text-gray-400">
          Enter your farm details to get ranked water shortage adaptation strategies
        </p>
      </div>

      {/* Main two-column layout */}
      <div className="flex h-[calc(100vh-73px)]">

        {/* Left column — input form, fixed width, scrollable */}
        <div className="w-[420px] shrink-0 border-r border-gray-200 bg-white overflow-y-auto p-6">
          <InputForm onSubmit={handleSubmit} />
        </div>

        {/* Right column — results, fills remaining space, scrollable */}
        <div className="flex-1 overflow-y-auto p-8">

          {/* Empty state — before any submission */}
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
              <StrategyResults results={results} />
              <CropTable results={results} userCrops={userCrops} />
            </div>
          )}

        </div>
      </div>
    </div>
  )
}