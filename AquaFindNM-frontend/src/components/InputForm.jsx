import { useState } from 'react'

const CROPS = ['pecan', 'alfalfa', 'corn', 'wheat', 'peppers', 'cotton', 'onions', 'beans']
const DISTRICTS = ['EBID (Dona Ana / Sierra County)', 'MRGCD (Bernalillo / Socorro County)']
const TRADING_OPTIONS = [
  { value: 'interdistrict', label: 'Full trading — can buy/sell across districts' },
  { value: 'intradistrict', label: 'Limited trading — within my district only' },
  { value: 'no_trade', label: 'No trading — proportional shortage sharing' },
]

export default function InputForm({ onSubmit }) {
  const [district, setDistrict] = useState('')
  const [shortage, setShortage] = useState(25)
  const [trading, setTrading] = useState('')
  const [crops, setCrops] = useState({})

  const handleCropAcres = (crop, acres) => {
    setCrops(prev => ({ ...prev, [crop]: Number(acres) }))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit({ district, shortage, trading, crops })
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-6 p-6 bg-white rounded-xl shadow">
      
      {/* District */}
      <div>
        <label className="block font-semibold mb-1">Your Irrigation District</label>
        <select
          className="w-full border rounded p-2"
          value={district}
          onChange={e => setDistrict(e.target.value)}
          required
        >
          <option value="">Select district...</option>
          {DISTRICTS.map(d => <option key={d} value={d}>{d}</option>)}
        </select>
      </div>

      {/* Shortage slider */}
      <div>
        <label className="block font-semibold mb-1">
          Expected Water Shortage: <span className="text-blue-600">{shortage}%</span>
        </label>
        <input
          type="range" min={0} max={60} step={5}
          value={shortage}
          onChange={e => setShortage(Number(e.target.value))}
          className="w-full"
        />
        <div className="flex justify-between text-sm text-gray-400">
          <span>0% (normal)</span><span>60% (severe)</span>
        </div>
      </div>

      {/* Trading institution */}
      <div>
        <label className="block font-semibold mb-1">Water Trading Access</label>
        {TRADING_OPTIONS.map(opt => (
          <label key={opt.value} className="flex items-center gap-2 mb-1">
            <input
              type="radio"
              name="trading"
              value={opt.value}
              checked={trading === opt.value}
              onChange={() => setTrading(opt.value)}
              required
            />
            {opt.label}
          </label>
        ))}
      </div>

      {/* Crop acres */}
      <div>
        <label className="block font-semibold mb-2">Your Crops and Acreage</label>
        <div className="grid grid-cols-2 gap-2">
          {CROPS.map(crop => (
            <div key={crop} className="flex items-center gap-2">
              <label className="capitalize w-20 text-sm">{crop}</label>
              <input
                type="number"
                min={0}
                placeholder="acres"
                className="border rounded p-1 w-24 text-sm"
                onChange={e => handleCropAcres(crop, e.target.value)}
              />
            </div>
          ))}
        </div>
      </div>

      <button
        type="submit"
        className="bg-blue-600 text-white rounded-lg py-2 font-semibold hover:bg-blue-700 transition"
      >
        Get Recommendations
      </button>
    </form> 
  )
}