# models/schemas.py
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class County(str, Enum):
    DONA_ANA = "dona_ana"
    SIERRA = "sierra"
    SOCORRO = "socorro"
    VALENCIA = "valencia"
    BERNALILLO = "bernalillo"
    SANDOVAL = "sandoval"

class TradingInstitution(str, Enum):
    UNLIMITED = "unlimited"
    LIMITED = "limited"
    NONE = "none"

class CropInput(BaseModel):
    crop: str
    acres: float = Field(gt=0, description="Acres currently in production")

class RecommendationRequest(BaseModel):
    county: County
    crops: list[CropInput]
    shortage_pct: float = Field(
        ge=0, le=60,
        description="Expected water shortage as % of normal supply (e.g., 25 means 75% of normal)"
    )
    trading_institution: TradingInstitution
    current_lease_price: Optional[float] = Field(
        None,
        description="Current market price for water lease in $/acre-ft. If None, uses literature range."
    )

class CropRecommendation(BaseModel):
    crop: str
    current_acres: float
    recommended_acres: float
    acres_to_fallow: float
    income_at_risk: float
    shadow_price: float
    action: str  # "maintain", "reduce", "fallow", "consider_buying_water"
    explanation: str

class StrategyComparison(BaseModel):
    institution: str
    income_preserved_pct: float
    estimated_income_loss_usd: float
    description: str

class BuyVsFallowAnalysis(BaseModel):
    crop: str
    shadow_price: float
    current_lease_price_used: float
    recommendation: str  # "buy_water", "fallow", "borderline"
    net_benefit_of_buying: float
    explanation: str

class RecommendationResponse(BaseModel):
    county: str
    shortage_pct: float
    trading_institution: str
    total_baseline_income: float
    estimated_income_loss: float
    income_preservation_pct: float
    crop_recommendations: list[CropRecommendation]
    strategy_comparison: list[StrategyComparison]
    buy_vs_fallow: list[BuyVsFallowAnalysis]
    headline_recommendation: str
    data_source_note: str
    
# Add to models/schemas.py

class DroughtStatus(BaseModel):
    county: str
    drought_category: str
    suggested_shortage_pct: float
    description: str
    data_date: Optional[str]
    source: str

class LiveContext(BaseModel):
    drought: DroughtStatus
    prices: dict
    et: dict
    data_freshness_note: str

# Update RecommendationRequest to add live data flag
class RecommendationRequest(BaseModel):
    county: County
    crops: list[CropInput]
    shortage_pct: float = Field(ge=0, le=60)
    trading_institution: TradingInstitution
    current_lease_price: Optional[float] = None
    use_live_data: bool = Field(
        default=False,
        description="If True, fetches current ET from OpenET and prices from USDA NASS"
    )

# Add live data fields to RecommendationResponse
class RecommendationResponse(BaseModel):
    county: str
    shortage_pct: float
    trading_institution: str
    total_baseline_income: float
    estimated_income_loss: float
    income_preservation_pct: float
    crop_recommendations: list[CropRecommendation]
    strategy_comparison: list[StrategyComparison]
    buy_vs_fallow: list[BuyVsFallowAnalysis]
    headline_recommendation: str
    data_source_note: str
    live_data_used: bool = False
    live_context: Optional[dict] = None