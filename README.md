# Water Optix
A decision-support tool that helps farmers and water managers identify the lowest-cost strategies for adapting to water shortages in the Rio Grande Basin. Created by ***Allison Barricklow, Hailey Hudson,*** and ***Shokhina Jalilova***, Built at DesertDevLab Hackathon — 04/18-19/2026.

## Problem Statement
heyy....

## Solution
hey...

## Research Behind it
how yall doing...

---

## Tech Stack
| Layer | Technology |
|-------|-----------|
| Frontend | React + Vite |
| Styling | Tailwind CSS |
| Charts | Recharts |
| Icons | Lucide React |
| Backend | Python + FastAPI |
| Data | Ward et al. 2025 scenario tables |

---

## Run it Locally

### Prequisites
- Node.js 18+
- Python 3.11+

### Environment Variables

Create a `.env` file in the frontend directory:

### Frontend
```bash
cd AquaFindNM-frontend
npm install
npm run dev
```

Runs at `http://localhost:5173`

### Backend
```bash
cd water_adapt/backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Runs at  `http://localhost:5713`

---

## Project Structure
DevLabHackathon/
├── AquaFindNM-frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── InputForm.jsx        # 4 farmer inputs
│   │   │   ├── StrategyResults.jsx  # ranked strategy cards
│   │   │   ├── IncomeChart.jsx      # recharts bar chart
│   │   │   ├── CropTable.jsx        # acreage adjustment table
│   │   │   ├── SeverityBanner.jsx   # drought severity indicator
│   │   │   └── FadeIn.jsx           # animation wrapper
│   │   ├── pages/
│   │   │   └── Home.jsx             # main layout
│   │   └── services/
│   │       └── api.js               # FastAPI connection
│   └── index.html

---

## Team

| Name | Role |
|------|------|
| Hailey Hudson | Frontend |
| Shokhina Jalilova | Backend/Data |
| Allison Barricklow | Prodcut Management/Full Stack Ops |

