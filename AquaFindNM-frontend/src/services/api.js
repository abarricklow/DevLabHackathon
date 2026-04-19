const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000"

export async function getRecommendation(formData) {
  const response = await fetch(`${BASE_URL}/recommend`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(formData)
  })
  if (!response.ok) throw new Error(`API error: ${response.status}`)
  return response.json()
}

export async function getCrops() {
  const response = await fetch(`${BASE_URL}/crops`)
  return response.json()
}

export async function getDroughtStatus(county) {
  const response = await fetch(`${BASE_URL}/drought/${county}`)
  return response.json()
}

export async function getShadowPrices(county, institution) {
  const response = await fetch(`${BASE_URL}/shadow-prices/${county}/${institution}`)
  return response.json()
}

export async function getLivePrices() {
  const response = await fetch(`${BASE_URL}/prices`)
  return response.json()
}