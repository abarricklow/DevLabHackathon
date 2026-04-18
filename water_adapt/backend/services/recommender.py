# services/recommender.py
import numpy as np
from data.scenarios import (
    NET_REVENUE_PER_ACRE,
    WATER_DEPTH_FT,
    BASELINE_ACRES,
    LAND_RETENTION_DROUGHT_25PCT,
    SHADOW_PRICES_DROUGHT_25PCT,
    INCOME_PRESERVATION,
    TOTAL_BASELINE_INCOME_USD,
    WATER_LEASE_PRICE_RANGE,
)
from models.schemas import (
    RecommendationRequest,
    RecommendationResponse,
    CropRecommendation,
    StrategyComparison,
    BuyVsFallowAnalysis,
)

# The paper only has one shortage scenario (25%). We interpolate
# linearly for other shortage levels using these anchor points.
# At 0% shortage, retention = 1.0 and shadow price = 0.
# At 25% shortage, use paper values.
# Beyond 25%, we extrapolate conservatively.
PAPER_SHORTAGE_PCT = 25.0

def interpolate_retention(paper_retention: float, shortage_pct: float) -> float:
    """
    Linear interpolation of land retention between 0% shortage (retention=1.0)
    and 25% shortage (paper value), then linear extrapolation beyond.
    """
    if shortage_pct <= 0:
        return 1.0
    ratio = shortage_pct / PAPER_SHORTAGE_PCT
    # At 0% shortage: full retention (1.0)
    # At 25% shortage: paper_retention
    interpolated = 1.0 + ratio * (paper_retention - 1.0)
    return max(0.0, min(1.0, interpolated))

def interpolate_shadow_price(paper_shadow: float, shortage_pct: float) -> float:
    """
    Shadow prices scale roughly linearly with shortage severity.
    At 0% shortage: shadow price = 0.
    At 25% shortage: paper value.
    """
    if shortage_pct <= 0:
        return 0.0
    ratio = shortage_pct / PAPER_SHORTAGE_PCT
    return paper_shadow * ratio

def get_action_and_explanation(
    crop: str,
    retention: float,
    shadow_price: float,
    lease_price: float,
) -> tuple[str, str]:
    """Translate numeric outputs into plain-language farmer guidance."""
    
    if retention < 0.05:
        action = "fallow"
        explanation = (
            f"Under current conditions, {crop} is not economically viable. "
            f"Water generates far more value reallocated to higher-value crops. "
            f"Consider fallowing and leasing your water allocation if trading is available."
        )
    elif shadow_price > lease_price * 1.2:
        action = "consider_buying_water"
        explanation = (
            f"Water is worth ${shadow_price:.2f}/acre-ft to your {crop} operation "
            f"but market leases are around ${lease_price:.2f}/acre-ft. "
            f"Buying additional water is economically justified."
        )
    elif retention >= 0.90:
        action = "maintain"
        explanation = (
            f"{crop.capitalize()} is a high-value crop that should maintain near-full acreage "
            f"even under shortage. Prioritize water allocation here."
        )
    elif retention >= 0.70:
        action = "reduce"
        explanation = (
            f"Reduce {crop} acreage by approximately {(1-retention)*100:.0f}%. "
            f"Focus remaining water on your highest-yielding fields."
        )
    else:
        action = "reduce"
        explanation = (
            f"Significant reduction in {crop} acreage recommended. "
            f"Water generates more income in other crops under current shortage conditions."
        )
    
    return action, explanation

def generate_recommendation(req: RecommendationRequest) -> RecommendationResponse:
    county = req.county.value
    institution = req.trading_institution.value
    shortage_pct = req.shortage_pct

    # Determine lease price to use
    if req.current_lease_price is not None:
        lease_price = req.current_lease_price
    else:
        lease_price = WATER_LEASE_PRICE_RANGE["mid"]

    crop_recommendations = []
    total_user_baseline_income = 0.0
    total_user_drought_income = 0.0
    buy_vs_fallow_analyses = []

    for crop_input in req.crops:
        crop = crop_input.crop.lower()
        user_acres = crop_input.acres

        # Get paper values for this crop/county/institution
        paper_retention = LAND_RETENTION_DROUGHT_25PCT[institution][crop][county]
        paper_shadow = SHADOW_PRICES_DROUGHT_25PCT[institution][crop][county]
        net_rev_per_acre = NET_REVENUE_PER_ACRE[crop][county]

        # Interpolate to actual shortage level
        retention = interpolate_retention(paper_retention, shortage_pct)
        shadow_price = interpolate_shadow_price(paper_shadow, shortage_pct)

        recommended_acres = user_acres * retention
        acres_to_fallow = user_acres - recommended_acres

        # Income calculations
        baseline_income = user_acres * net_rev_per_acre
        drought_income = recommended_acres * net_rev_per_acre
        income_at_risk = baseline_income - drought_income

        total_user_baseline_income += baseline_income
        total_user_drought_income += drought_income

        action, explanation = get_action_and_explanation(
            crop, retention, shadow_price, lease_price
        )

        crop_recommendations.append(CropRecommendation(
            crop=crop,
            current_acres=round(user_acres, 1),
            recommended_acres=round(recommended_acres, 1),
            acres_to_fallow=round(acres_to_fallow, 1),
            income_at_risk=round(income_at_risk, 2),
            shadow_price=round(shadow_price, 2),
            action=action,
            explanation=explanation,
        ))

        # Buy vs. fallow analysis for each crop
        water_needed = user_acres * WATER_DEPTH_FT[crop][county]
        water_to_buy_for_full_crop = acres_to_fallow * WATER_DEPTH_FT[crop][county]
        cost_to_buy = water_to_buy_for_full_crop * lease_price
        income_saved_by_buying = income_at_risk
        net_benefit = income_saved_by_buying - cost_to_buy

        if net_benefit > 500:
            bvf_rec = "buy_water"
            bvf_explanation = (
                f"Buying ~{water_to_buy_for_full_crop:.0f} acre-ft at ${lease_price:.2f}/acre-ft "
                f"costs ${cost_to_buy:,.0f} but preserves ${income_saved_by_buying:,.0f} in {crop} income. "
                f"Net benefit: ${net_benefit:,.0f}."
            )
        elif net_benefit < -500:
            bvf_rec = "fallow"
            bvf_explanation = (
                f"Buying water for {crop} costs ${cost_to_buy:,.0f} but only preserves "
                f"${income_saved_by_buying:,.0f} in income. Fallowing saves ${abs(net_benefit):,.0f}."
            )
        else:
            bvf_rec = "borderline"
            bvf_explanation = (
                f"The economics are close for {crop}. Consider your cash flow position "
                f"and whether water is actually available to lease nearby."
            )

        buy_vs_fallow_analyses.append(BuyVsFallowAnalysis(
            crop=crop,
            shadow_price=round(shadow_price, 2),
            current_lease_price_used=lease_price,
            recommendation=bvf_rec,
            net_benefit_of_buying=round(net_benefit, 2),
            explanation=bvf_explanation,
        ))

    # Strategy comparison across all three institutions
    strategy_comparison = []
    institution_labels = {
        "unlimited": "Unrestricted Water Trading (all crops and counties)",
        "limited": "Within-County Trading Only",
        "none": "Proportional Sharing — No Trading",
    }
    for inst, preservation in INCOME_PRESERVATION.items():
        estimated_loss = total_user_baseline_income * (1 - preservation)
        strategy_comparison.append(StrategyComparison(
            institution=inst,
            income_preserved_pct=round(preservation * 100, 2),
            estimated_income_loss_usd=round(estimated_loss, 2),
            description=institution_labels[inst],
        ))

    # Sort crop recommendations: fallow candidates last, maintain first
    action_order = {"maintain": 0, "consider_buying_water": 1, "reduce": 2, "fallow": 3}
    crop_recommendations.sort(key=lambda x: action_order.get(x.action, 4))

    estimated_loss = total_user_baseline_income - total_user_drought_income
    preservation_pct = (total_user_drought_income / total_user_baseline_income * 100
                        if total_user_baseline_income > 0 else 0)

    # Headline recommendation
    best_strategy = min(strategy_comparison, key=lambda x: x.estimated_income_loss_usd)
    fallow_crops = [r.crop for r in crop_recommendations if r.action == "fallow"]
    buy_crops = [r.crop for r in crop_recommendations if r.action == "consider_buying_water"]

    headline_parts = [
        f"Under a {shortage_pct:.0f}% water shortage with {institution_labels[institution]}, "
        f"you can preserve approximately {preservation_pct:.1f}% of your baseline income."
    ]
    if fallow_crops:
        headline_parts.append(f"Consider fallowing: {', '.join(fallow_crops)}.")
    if buy_crops:
        headline_parts.append(f"Buying water is economically justified for: {', '.join(buy_crops)}.")

    return RecommendationResponse(
        county=county,
        shortage_pct=shortage_pct,
        trading_institution=institution,
        total_baseline_income=round(total_user_baseline_income, 2),
        estimated_income_loss=round(estimated_loss, 2),
        income_preservation_pct=round(preservation_pct, 2),
        crop_recommendations=crop_recommendations,
        strategy_comparison=strategy_comparison,
        buy_vs_fallow=buy_vs_fallow_analyses,
        headline_recommendation=" ".join(headline_parts),
        data_source_note=(
            "Recommendations calibrated to Ward et al. (2025) Agricultural Water Management "
            "and Ward (2025) Water Resources Management, Rio Grande Basin, New Mexico. "
            "Results interpolated from a 25% shortage scenario. Use as decision-support guidance."
        ),
    )