import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const getRecommendation = async (farmData) => {
  const response = await axios.post(`${BASE_URL}/recommend`, farmData)
  return response.data
}