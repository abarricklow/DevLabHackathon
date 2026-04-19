# Water Optix
A decision-support tool that helps farmers and water managers identify the lowest-cost strategies for adapting to water shortages in the Rio Grande Basin. Created by ***Allison Barricklow, Hailey Hudson,*** and ***Shokhina Jalilova***, Built at DesertDevLab Hackathon — 04/18-19/2026.

## Problem Statement
Water scarcity is accelerating across the American Southwest. Farmers facing drought shortages must make high-stakes decisions with little analytical support:

- Should I fallow land or buy water on the market?
- Which crops should I prioritize when supply is cut?
- Is it worth investing in trading arrangements with neighboring districts?

These decisions have massive income implications — yet most farmers make them without any structured economic guidance.

## Solution
The Drought Adaptation Advisor translates peer-reviewed hydro-economic research
from New Mexico State University into an accessible decision tool. A farmer
enters four inputs:

1. **Irrigation district** — EBID or MRGCD in the Rio Grande Basin
2. **Expected shortage level** — what % below normal supply they anticipate
3. **Water trading access** — what institutional arrangements are available
4. **Crop portfolio** — which crops they grow and how many acres

The platform returns:
- Ranked adaptation strategies by income preserved
- Crop-by-crop acreage adjustment recommendations
- A visual income comparison across trading institutions
- A plain-English buy vs. fallow recommendation based on shadow prices

## Research Behind It

This tool is grounded in original hydro-economic optimization research published
in *Water Resources Management* (2025):

> Ward, F.A. (2025). Addressing Global Water Challenges in 2025: An Integrated
> Framework for Research, Policy, and Resource Management.
> *Water Resources Management.*
> https://doi.org/10.1007/s11269-025-04341-0

The model uses **Positive Mathematical Programming (PMP)** to simulate
interdistrict and intradistrict water trading under drought across two New Mexico
irrigation districts:

- **EBID** — Elephant Butte Irrigation District (Dona Ana / Sierra County)
- **MRGCD** — Middle Rio Grande Conservancy District (Bernalillo / Socorro County)

Shadow prices, income preservation percentages, and crop acreage adjustments
surfaced in the UI are derived directly from the paper's optimization results
across five years of observed data (2017–2021).

---

## Running Locally

### Prerequisites
- Node.js 18+
- Python 3.11+

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Runs at `http://localhost:5173`

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Runs at `http://localhost:8000`

### Environment Variables

Create a `.env` file in the frontend directory:

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
│   │   ├── pages/   
│   │   └── services/  
│   └── index.html  
├──water_adapt/backend/    
│   ├── data/  
│   ├── models/  
│   ├── services/  
│   └── main.py   
</pre>
---

## Team

| Name | Role |
|------|------|
| Hailey Hudson | Frontend |
| Shokhina Jalilova | Backend/Data |
| Allison Barricklow | Product Management |

---

## Acknowledgements

Research foundation provided by **Dr. Frank A. Ward**, Professor at New Mexico
State University, whose hydro-economic modeling of the Rio Grande Basin made
this tool possible.

