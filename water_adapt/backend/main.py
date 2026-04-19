# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models.schemas import RecommendationRequest, RecommendationResponse
from services.recommender import generate_recommendation
from services.external_data import (
    get_drought_status,
    get_current_crop_prices,
    get_current_et,
    get_live_context,
    FALLBACK_PRICES,          # <-- this was missing
)

app = FastAPI(
    title="Water Adaptation Decision Platform",
    description="Ranks drought adaptation strategies by economic impact, calibrated to Ward et al. (2025)",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "running", "docs": "/docs"}

@app.get("/crops")
def list_crops():
    return {
        "crops": ["pecan", "alfalfa", "corn", "wheat", "peppers", "cotton", "onions"],
        "counties": ["dona_ana", "sierra", "socorro", "valencia", "bernalillo", "sandoval"],
        "institutions": ["unlimited", "limited", "none"]
    }

@app.post("/recommend", response_model=RecommendationResponse)
def recommend(req: RecommendationRequest):
    valid_crops = ["pecan", "alfalfa", "corn", "wheat", "peppers", "cotton", "onions"]
    for crop_input in req.crops:
        if crop_input.crop.lower() not in valid_crops:
            raise HTTPException(
                status_code=400,
                detail=f"Crop '{crop_input.crop}' not in dataset. Valid crops: {valid_crops}"
            )
    return generate_recommendation(req)

@app.get("/shadow-prices/{county}/{institution}")
def get_shadow_prices(county: str, institution: str):
    from data.scenarios import SHADOW_PRICES_DROUGHT_25PCT
    if institution not in SHADOW_PRICES_DROUGHT_25PCT:
        raise HTTPException(status_code=400, detail="Invalid institution")
    prices = {}
    for crop, counties in SHADOW_PRICES_DROUGHT_25PCT[institution].items():
        if county in counties:
            prices[crop] = counties[county]
    if not prices:
        raise HTTPException(status_code=404, detail="County not found")
    return {"county": county, "institution": institution, "shadow_prices": prices}

@app.get("/drought/{county}")
def drought_status(county: str):
    valid_counties = ["dona_ana", "sierra", "socorro",
                      "valencia", "bernalillo", "sandoval"]
    if county not in valid_counties:
        raise HTTPException(status_code=400, detail="Invalid county")
    return get_drought_status(county)

@app.get("/prices")
def current_prices():
    live = get_current_crop_prices()
    
    # Guard against None return from external_data
    if not live:
        return {
            "error": "Could not fetch live prices",
            "fallback_prices": FALLBACK_PRICES
        }
    
    comparison = {}
    for crop, live_price in live.items():
        baseline = FALLBACK_PRICES.get(crop, live_price)  # .get() instead of [] for safety
        if baseline == 0:
            continue
        pct_change = ((live_price - baseline) / baseline) * 100
        comparison[crop] = {
            "current_net_revenue_per_acre": live_price,
            "paper_2022_baseline": baseline,
            "pct_change_from_baseline": round(pct_change, 1),
            "direction": "higher" if pct_change > 0 else "lower",
        }
    return comparison

@app.get("/et/{county}/{crop}")
def current_et(county: str, crop: str):
    valid_crops = ["pecan", "alfalfa", "corn", "wheat",
                   "peppers", "cotton", "onions"]
    valid_counties = ["dona_ana", "sierra", "socorro",
                      "valencia", "bernalillo", "sandoval"]
    if county not in valid_counties:
        raise HTTPException(status_code=400, detail="Invalid county")
    if crop not in valid_crops:
        raise HTTPException(status_code=400, detail="Invalid crop")

    from data.scenarios import WATER_DEPTH_FT
    live_et = get_current_et(county, crop)
    baseline_et = WATER_DEPTH_FT[crop][county]
    pct_change = ((live_et - baseline_et) / baseline_et) * 100

    return {
        "county": county,
        "crop": crop,
        "current_et_feet": live_et,
        "baseline_2022_feet": baseline_et,
        "pct_change": round(pct_change, 1),
        "interpretation": (
            f"Current ET is {abs(pct_change):.1f}% "
            f"{'higher' if pct_change > 0 else 'lower'} than 2022 baseline. "
            f"{'Drought stress is reducing crop water use.' if pct_change < -10 else ''}"
            f"{'Higher temperatures are increasing water demand.' if pct_change > 10 else ''}"
        )
    }