# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models.schemas import RecommendationRequest, RecommendationResponse
from services.recommender import generate_recommendation

app = FastAPI(
    title="Water Adaptation Decision Platform",
    description="Ranks drought adaptation strategies by economic impact, calibrated to Ward et al. (2025)",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this in production
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
    """Expose raw shadow prices for a county and institution — useful for frontend charts."""
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