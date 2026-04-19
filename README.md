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

Create a `.venv` file in the project directory:

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

Runs at  `http://localhost:8000`

---

## Project Structure
<pre>
DevLabHackathon/  
├──AquaFindNM-frontend/  
│   ├── src/  
│   │   ├── components/  
│   │   │   ├── InputForm.jsx  
│   │   │   ├── StrategyResults.jsx  
│   │   │   ├── IncomeChart.jsx  
│   │   │   ├── CropTable.jsx  
│   │   │   ├── SeverityBanner.jsx  
│   │   │   └── FadeIn.jsx  
│   │   ├── pages/  
│   │   │   └── Home.jsx  
│   │   └── services/  
│   │       └── api.js  
│   └── index.html  
</pre>
---

## Team

| Name | Role |
|------|------|
| Hailey Hudson | Frontend |
| Shokhina Jalilova | Backend/Data |
| Allison Barricklow | Prodcut Management/Full Stack Ops |

