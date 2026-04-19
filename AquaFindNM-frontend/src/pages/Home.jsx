import { useState } from 'react'
import { getRecommendation } from '../services/api'    // make sure this path matches yours
import InputForm from '../components/InputForm'
import StrategyResults from '../components/StrategyResults'
import CropTable from '../components/CropTable'
import IncomeChart from '../components/IncomeChart'
import FadeIn from '../components/FadeIn'
import SeverityBanner from '../components/SeverityBanner'

export default function Home() {
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [shortage, setShortage] = useState(null)

  const handleSubmit = async (farmData) => {
    setLoading(true)
    setError(null)
    setShortage(farmData.shortage_pct)

    try {
      // farmData is already in the exact shape the backend expects
      // because InputForm now formats it correctly before calling onSubmit
      const data = await getRecommendation(farmData)
      setResults(data)
    } catch (err) {
      console.error('API error:', err)
      setError('Could not get recommendations. Make sure the backend is running.')
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setResults(null)
    setError(null)
    setShortage(null)
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
                <CropTable results={results} />
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