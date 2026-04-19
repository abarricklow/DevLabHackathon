# services/recommender.py
"""
Core recommendation engine for the Water Adaptation Decision Platform.

This module takes a user's crop portfolio, county, shortage level, and
water trading institution, then produces ranked adaptation strategies
with income impact estimates.

Data source: Ward et al. (2025) Agricultural Water Management and
Ward (2025) Water Resources Management — Rio Grande Basin, New Mexico.

Key concepts:
- Shadow price: marginal value of one acre-foot of water ($/acre-ft)
  High shadow price = water is scarce for this crop, buying is worth it
  Low shadow price = crop doesn't need water badly, fallow it

- Land retention: proportion of historical acreage that survives drought
  Under market trading: high-value crops retain near 100%, low-value near 0%
  Under proportional sharing: all crops retain exactly (1 - shortage_pct/100)

- Income preservation: fraction of baseline income maintained under drought
  Unlimited trading always >= limited trading >= proportional sharing
"""

from data.scenarios import (
    NET_REVENUE_PER_ACRE,
    WATER_DEPTH_FT,
    BASELINE_ACRES,
    LAND_RETENTION_DROUGHT_25PCT,
    SHADOW_PRICES_DROUGHT_25PCT,
    INCOME_PRESERVATION,
    WATER_LEASE_PRICE_RANGE,
)
from models.schemas import (
    RecommendationRequest,
    RecommendationResponse,
    CropRecommendation,
    StrategyComparison,
    BuyVsFallowAnalysis,
)

# ─────────────────────────────────────────────────────────────
# INTERPOLATION LAYER
#
# The Ward paper only gives us results for exactly 25% shortage.
# We need to handle any shortage level the user enters.
# We use two anchor points:
#   - 0% shortage → retention = 1.0, shadow price = 0
#   - 25% shortage → paper values
#
# For shortages above 25%, we use a second extrapolation that
# accelerates the decline for low-value crops (they hit zero
# faster than linear would suggest) while high-value crops
# decline more slowly (farmers protect them at all costs).
# ─────────────────────────────────────────────────────────────

PAPER_SHORTAGE_PCT = 25.0

# These multipliers adjust how quickly each crop's retention
# falls beyond 25% shortage. Values > 1 mean faster decline
# (crop is vulnerable), values < 1 mean slower decline
# (crop is protected). Derived from the paper's crop value rankings.
CROP_VULNERABILITY_BEYOND_25PCT = {
    "pecan":   0.7,   # very high value, protected even in severe drought
    "alfalfa": 0.9,   # medium value, moderately protected
    "corn":    1.1,   # lower value, falls faster
    "wheat":   2.0,   # very low value, eliminated quickly
    "peppers": 0.6,   # highest value, most protected
    "cotton":  1.5,   # low value, falls faster
    "onions":  0.65,  # high value, well protected
}


def interpolate_retention(
    crop: str,
    institution: str,
    county: str,
    shortage_pct: float
) -> float:
    """
    Computes land retention fraction for any shortage level.

    Three zones:
    1. 0% to 25%: linear interpolation from 1.0 to paper value
    2. Above 25%: crop-specific extrapolation using vulnerability multipliers
    3. Any institution "none": always exactly (1 - shortage_pct/100)
       because proportional sharing means everyone takes the same cut

    Args:
        crop: crop name matching scenarios.py keys
        institution: "unlimited", "limited", or "none"
        county: county name matching scenarios.py keys
        shortage_pct: water shortage as percentage of normal supply

    Returns:
        float between 0.0 and 1.0 representing fraction of acres retained
    """
    if shortage_pct <= 0:
        return 1.0

    # Proportional sharing is always exact — everyone takes the same cut
    # regardless of crop value. This is the definition of "none" institution.
    if institution == "none":
        return max(0.0, 1.0 - (shortage_pct / 100.0))

    paper_retention = LAND_RETENTION_DROUGHT_25PCT[institution][crop][county]

    if shortage_pct <= PAPER_SHORTAGE_PCT:
        # Zone 1: linear interpolation between 0 and 25%
        # At 0% shortage: retention = 1.0
        # At 25% shortage: retention = paper_retention
        ratio = shortage_pct / PAPER_SHORTAGE_PCT
        retention = 1.0 + ratio * (paper_retention - 1.0)

    else:
        # Zone 2: extrapolation beyond 25%
        # Start from the paper value at 25% and apply crop-specific decline rate
        # The decline beyond 25% is faster for low-value crops
        excess_shortage = shortage_pct - PAPER_SHORTAGE_PCT
        vulnerability = CROP_VULNERABILITY_BEYOND_25PCT.get(crop, 1.0)

        # Each additional 1% shortage beyond 25% reduces retention by
        # (paper_retention / 25) * vulnerability
        # This means crops that were already near zero at 25% hit zero
        # quickly, while high-value crops decline slowly
        decline_per_pct = (paper_retention / PAPER_SHORTAGE_PCT) * vulnerability
        retention = paper_retention - (excess_shortage * decline_per_pct)

    return max(0.0, min(1.0, retention))


def interpolate_shadow_price(
    crop: str,
    institution: str,
    county: str,
    shortage_pct: float
) -> float:
    """
    Computes shadow price ($/acre-ft) for any shortage level.

    Shadow prices:
    - Are zero when there is no shortage (water is not scarce)
    - Increase as shortage worsens (water becomes more valuable)
    - Under unlimited trading, equalize across all crops/counties
    - Under no trading, vary wildly by crop (low for wheat, high for onions)

    The relationship is roughly linear but accelerates at severe shortages.
    We use a quadratic adjustment beyond 25% to capture this.

    Args:
        crop: crop name
        institution: trading institution
        county: county name
        shortage_pct: water shortage percentage

    Returns:
        float shadow price in $/acre-ft
    """
    if shortage_pct <= 0:
        return 0.0

    paper_shadow = SHADOW_PRICES_DROUGHT_25PCT[institution][crop][county]
    ratio = shortage_pct / PAPER_SHORTAGE_PCT

    if shortage_pct <= PAPER_SHORTAGE_PCT:
        # Linear scaling from 0 to paper value
        return round(paper_shadow * ratio, 2)
    else:
        # Beyond 25%, shadow prices accelerate (water scarcity is nonlinear)
        # Use ratio^1.3 to capture this acceleration
        return round(paper_shadow * (ratio ** 1.3), 2)


# ─────────────────────────────────────────────────────────────
# STRATEGY RANKER
#
# Given a user's situation, ranks ALL available adaptation
# strategies from best to worst by income preservation.
# This is the core "what should I do?" output.
#
# The four strategies we rank:
# 1. Unlimited interdistrict trading (best economic outcome)
# 2. Limited intradistrict trading (second best)
# 3. Proportional sharing, no trading (worst economic outcome)
# 4. Crop-specific fallowing (a variant of strategy 1/2 but
#    highlighting which specific crops to fallow first)
# ─────────────────────────────────────────────────────────────

def rank_strategies(
    county: str,
    crops: list[dict],   # list of {"crop": str, "acres": float}
    shortage_pct: float,
    current_lease_price: float,
    live_prices: dict = None,
    live_et: dict = None,
) -> list[StrategyComparison]:
    """
    Ranks all water shortage adaptation strategies by income preserved.

    For each of the three trading institutions, computes crop-level
    retention and income for the user's specific portfolio — not just
    the study-area aggregate from the paper.

    Args:
        county: user's county
        crops: list of {"crop": name, "acres": acreage} dicts
        shortage_pct: expected water shortage percentage
        current_lease_price: current water lease price $/acre-ft
        live_prices: optional dict of live crop prices from NASS
        live_et: optional dict of live ET values from OpenET

    Returns:
        List of StrategyComparison objects sorted by income_preserved descending
    """
    strategies = []

    for institution in ["unlimited", "limited", "none"]:
        total_baseline = 0.0
        total_drought = 0.0
        fallow_recommendations = []
        buy_recommendations = []

        for crop_data in crops:
            crop = crop_data["crop"]
            acres = crop_data["acres"]

            # Use live price if available, fall back to paper value
            if live_prices and crop in live_prices:
                net_rev = live_prices[crop]
            else:
                net_rev = NET_REVENUE_PER_ACRE[crop][county]

            # Use live ET if available
            if live_et and crop in live_et:
                et_feet = live_et[crop]
            else:
                et_feet = WATER_DEPTH_FT[crop][county]

            retention = interpolate_retention(crop, institution, county, shortage_pct)
            shadow_price = interpolate_shadow_price(crop, institution, county, shortage_pct)

            baseline_income = acres * net_rev
            drought_income = acres * retention * net_rev

            total_baseline += baseline_income
            total_drought += drought_income

            # Track which crops should be fallowed under this institution
            if retention < 0.15:
                fallow_recommendations.append(f"{crop} ({retention*100:.0f}% retained)")

            # Track which crops benefit from buying water
            if shadow_price > current_lease_price * 1.1:
                water_to_buy = acres * (1 - retention) * et_feet
                buy_cost = water_to_buy * current_lease_price
                income_preserved = acres * (1 - retention) * net_rev
                if income_preserved > buy_cost:
                    buy_recommendations.append(crop)

        income_loss = total_baseline - total_drought
        preservation_pct = (
            (total_drought / total_baseline * 100) if total_baseline > 0 else 0
        )

        # Build human-readable description for each institution
        description = _build_strategy_description(
            institution, shortage_pct, preservation_pct,
            income_loss, fallow_recommendations, buy_recommendations
        )

        institution_labels = {
            "unlimited": "Unrestricted Water Trading — all crops and counties",
            "limited":   "Within-County Trading Only — reduced admin cost",
            "none":      "Proportional Sharing — no water trading",
        }

        strategies.append(StrategyComparison(
            institution=institution,
            income_preserved_pct=round(preservation_pct, 2),
            estimated_income_loss_usd=round(income_loss, 2),
            description=institution_labels[institution],
            detailed_description=description,
            fallow_these_crops=fallow_recommendations,
            buy_water_for_these_crops=buy_recommendations,
        ))

    # Sort by income preserved descending — best strategy first
    strategies.sort(key=lambda x: x.income_preserved_pct, reverse=True)

    return strategies


def _build_strategy_description(
    institution: str,
    shortage_pct: float,
    preservation_pct: float,
    income_loss: float,
    fallow_crops: list,
    buy_crops: list,
) -> str:
    """Builds a plain-English explanation of each strategy."""

    base_descriptions = {
        "unlimited": (
            f"Water trades freely across all counties and crops. "
            f"Market forces move water to highest-value uses. "
            f"Requires water rights infrastructure and trading agreements."
        ),
        "limited": (
            f"Water trades within your county only. "
            f"Lower administrative complexity than full market trading. "
            f"Good balance of efficiency and feasibility."
        ),
        "none": (
            f"Every crop takes a {shortage_pct:.0f}% water cut equally. "
            f"Simple to administer but economically inefficient — "
            f"low-value crops get water they can barely use while "
            f"high-value crops are severely constrained."
        ),
    }

    desc = base_descriptions[institution]
    desc += f" Preserves {preservation_pct:.1f}% of baseline income (loss: ${income_loss:,.0f})."

    if fallow_crops and institution != "none":
        desc += f" Market forces would eliminate: {', '.join(fallow_crops)}."

    if buy_crops and institution != "none":
        desc += f" Buying water is economically justified for: {', '.join(buy_crops)}."

    return desc


# ─────────────────────────────────────────────────────────────
# BUY VS FALLOW CALCULATOR
#
# For each crop, answers: given that I'm losing some acreage to
# shortage, should I buy water on the market to maintain that
# acreage, or should I fallow it and save the water cost?
#
# The math:
#   Cost to buy = (acres_to_fallow × ET_per_acre) × lease_price
#   Income preserved = acres_to_fallow × net_revenue_per_acre
#   Net benefit of buying = income_preserved - cost_to_buy
#
# We also add a partial buying analysis — you don't have to
# buy water for ALL your fallowed acres. We find the optimal
# number of acres to buy water for.
# ─────────────────────────────────────────────────────────────

def calculate_buy_vs_fallow(
    crop: str,
    county: str,
    institution: str,
    shortage_pct: float,
    user_acres: float,
    current_lease_price: float,
    live_prices: dict = None,
    live_et: dict = None,
) -> BuyVsFallowAnalysis:
    """
    Determines whether buying water is economically justified for a crop.

    Three possible outcomes:
    - "buy_water": buying is clearly profitable (net benefit > 10% of income)
    - "fallow": buying costs more than it saves
    - "borderline": within 10% either way — context-dependent decision

    Also calculates the OPTIMAL partial buy — sometimes you should buy
    water for some fallowed acres but not all of them.

    Args:
        crop: crop name
        county: county name
        institution: current trading institution
        shortage_pct: shortage percentage
        user_acres: user's total acreage of this crop
        current_lease_price: $/acre-ft water lease price
        live_prices: optional live price data
        live_et: optional live ET data

    Returns:
        BuyVsFallowAnalysis with recommendation and financial details
    """
    # Get current values (live if available, paper fallback)
    net_rev = (
        live_prices.get(crop) if live_prices and crop in live_prices
        else NET_REVENUE_PER_ACRE[crop][county]
    )
    et_feet = (
        live_et.get(crop) if live_et and crop in live_et
        else WATER_DEPTH_FT[crop][county]
    )

    retention = interpolate_retention(crop, institution, county, shortage_pct)
    shadow_price = interpolate_shadow_price(crop, institution, county, shortage_pct)

    recommended_acres = user_acres * retention
    acres_at_risk = user_acres - recommended_acres

    # If nothing is being fallowed, no buy decision needed
    if acres_at_risk < 0.5:
        return BuyVsFallowAnalysis(
            crop=crop,
            shadow_price=round(shadow_price, 2),
            current_lease_price_used=current_lease_price,
            recommendation="maintain",
            acres_to_buy_water_for=0.0,
            water_volume_to_buy_acre_ft=0.0,
            cost_to_buy=0.0,
            income_preserved_by_buying=0.0,
            net_benefit_of_buying=0.0,
            explanation=(
                f"{crop.capitalize()} maintains {retention*100:.1f}% of acreage "
                f"under current conditions. No water purchase needed."
            ),
            breakeven_lease_price=round(shadow_price, 2),
        )

    # Full buy analysis: what if you buy water for ALL fallowed acres?
    water_for_full_buy = acres_at_risk * et_feet
    cost_for_full_buy = water_for_full_buy * current_lease_price
    income_from_full_buy = acres_at_risk * net_rev
    net_benefit_full = income_from_full_buy - cost_for_full_buy

    # Partial buy analysis: find optimal acres to buy water for
    # The breakeven point is where income per acre = water cost per acre
    # income_per_acre = net_rev
    # water_cost_per_acre = et_feet × lease_price
    # Buy if net_rev > et_feet × lease_price
    income_per_acre = net_rev
    water_cost_per_acre = et_feet * current_lease_price

    if income_per_acre > water_cost_per_acre:
        # Profitable to buy water for ALL fallowed acres
        optimal_acres_to_buy = acres_at_risk
    else:
        # Not profitable — buying water for any acre costs more than it saves
        optimal_acres_to_buy = 0.0

    # Calculate figures for the optimal (partial) buy
    optimal_water_volume = optimal_acres_to_buy * et_feet
    optimal_cost = optimal_water_volume * current_lease_price
    optimal_income_preserved = optimal_acres_to_buy * net_rev
    optimal_net_benefit = optimal_income_preserved - optimal_cost

    # Breakeven lease price: the price at which buying becomes unprofitable
    # net_rev = et_feet × breakeven_price → breakeven = net_rev / et_feet
    breakeven_price = net_rev / et_feet if et_feet > 0 else 0.0

    # Determine recommendation with confidence threshold
    benefit_ratio = optimal_net_benefit / max(income_from_full_buy, 1)

    if optimal_acres_to_buy > 0 and benefit_ratio > 0.10:
        recommendation = "buy_water"
    elif optimal_acres_to_buy == 0 or benefit_ratio < -0.10:
        recommendation = "fallow"
    else:
        recommendation = "borderline"

    explanation = _build_buy_fallow_explanation(
        crop, shadow_price, current_lease_price, breakeven_price,
        optimal_acres_to_buy, acres_at_risk, optimal_cost,
        optimal_income_preserved, optimal_net_benefit, recommendation
    )

    return BuyVsFallowAnalysis(
        crop=crop,
        shadow_price=round(shadow_price, 2),
        current_lease_price_used=current_lease_price,
        recommendation=recommendation,
        acres_to_buy_water_for=round(optimal_acres_to_buy, 1),
        water_volume_to_buy_acre_ft=round(optimal_water_volume, 1),
        cost_to_buy=round(optimal_cost, 2),
        income_preserved_by_buying=round(optimal_income_preserved, 2),
        net_benefit_of_buying=round(optimal_net_benefit, 2),
        explanation=explanation,
        breakeven_lease_price=round(breakeven_price, 2),
    )


def _build_buy_fallow_explanation(
    crop: str,
    shadow_price: float,
    lease_price: float,
    breakeven_price: float,
    optimal_acres: float,
    total_at_risk_acres: float,
    cost: float,
    income_preserved: float,
    net_benefit: float,
    recommendation: str,
) -> str:
    """Builds plain-English explanation for buy vs fallow decision."""

    if recommendation == "maintain":
        return f"{crop.capitalize()} is maintaining near-full acreage. No water purchase needed."

    if recommendation == "buy_water":
        return (
            f"Buying water for {optimal_acres:.0f} acres of {crop} "
            f"costs ${cost:,.0f} ({optimal_acres * WATER_DEPTH_FT.get(crop, {}).get('dona_ana', 3):.0f} "
            f"acre-ft × ${lease_price:.2f}/acre-ft) but preserves "
            f"${income_preserved:,.0f} in income. "
            f"Net benefit: ${net_benefit:,.0f}. "
            f"Buying remains profitable as long as lease prices stay below "
            f"${breakeven_price:.2f}/acre-ft."
        )

    if recommendation == "fallow":
        loss_from_buying = abs(net_benefit)
        return (
            f"Buying water for {crop} is not justified at ${lease_price:.2f}/acre-ft. "
            f"Water costs ${lease_price:.2f}/acre-ft but only generates "
            f"${(income_preserved / max(optimal_acres * WATER_DEPTH_FT.get(crop, {}).get('dona_ana', 3), 1)):.2f} "
            f"in income per acre-ft. "
            f"Fallow {total_at_risk_acres:.0f} acres and save ${loss_from_buying:,.0f}. "
            f"Buying would become profitable if lease prices fell below "
            f"${breakeven_price:.2f}/acre-ft."
        )

    # borderline
    return (
        f"The economics are close for {crop}. "
        f"Water is worth ${shadow_price:.2f}/acre-ft to this crop "
        f"vs ${lease_price:.2f}/acre-ft market lease. "
        f"Net benefit of buying: ${net_benefit:,.0f}. "
        f"Consider your cash flow, whether water is available nearby, "
        f"and whether prices might change. "
        f"Breakeven lease price: ${breakeven_price:.2f}/acre-ft."
    )


# ─────────────────────────────────────────────────────────────
# CROP-LEVEL RECOMMENDATIONS
# ─────────────────────────────────────────────────────────────

def build_crop_recommendation(
    crop: str,
    county: str,
    institution: str,
    shortage_pct: float,
    user_acres: float,
    current_lease_price: float,
    live_prices: dict = None,
    live_et: dict = None,
) -> CropRecommendation:
    """
    Builds a complete recommendation for a single crop.
    Combines retention analysis, income impact, and action label.
    """
    net_rev = (
        live_prices.get(crop) if live_prices and crop in live_prices
        else NET_REVENUE_PER_ACRE[crop][county]
    )

    retention = interpolate_retention(crop, institution, county, shortage_pct)
    shadow_price = interpolate_shadow_price(crop, institution, county, shortage_pct)

    recommended_acres = user_acres * retention
    acres_to_fallow = user_acres - recommended_acres
    baseline_income = user_acres * net_rev
    drought_income = recommended_acres * net_rev
    income_at_risk = baseline_income - drought_income

    action, explanation = _determine_action(
        crop, retention, shadow_price, current_lease_price,
        income_at_risk, institution, shortage_pct
    )

    # Flag if live prices differ significantly from paper baseline
    paper_price = NET_REVENUE_PER_ACRE[crop][county]
    price_change_note = None
    if live_prices and crop in live_prices:
        live_price = live_prices[crop]
        pct_change = ((live_price - paper_price) / paper_price) * 100
        if abs(pct_change) > 15:
            direction = "risen" if pct_change > 0 else "fallen"
            price_change_note = (
                f"Note: {crop.capitalize()} prices have {direction} "
                f"{abs(pct_change):.0f}% since the 2022 study baseline "
                f"(${paper_price:.0f} → ${live_price:.0f}/acre). "
                f"This {'strengthens' if pct_change > 0 else 'weakens'} "
                f"the case for protecting this crop."
            )

    return CropRecommendation(
        crop=crop,
        current_acres=round(user_acres, 1),
        recommended_acres=round(recommended_acres, 1),
        acres_to_fallow=round(acres_to_fallow, 1),
        income_at_risk=round(income_at_risk, 2),
        shadow_price=round(shadow_price, 2),
        action=action,
        explanation=explanation,
        price_change_note=price_change_note,
        using_live_price=bool(live_prices and crop in live_prices),
    )


def _determine_action(
    crop: str,
    retention: float,
    shadow_price: float,
    lease_price: float,
    income_at_risk: float,
    institution: str,
    shortage_pct: float,
) -> tuple[str, str]:
    """
    Translates numeric outputs into a single action label and explanation.

    Action hierarchy (checked in order):
    1. fallow — retention below 5%, not worth maintaining
    2. consider_buying_water — shadow price well above lease price
    3. maintain — high-value crop retaining >90% acreage
    4. reduce — moderate reduction needed
    """
    if retention < 0.05:
        return "fallow", (
            f"{crop.capitalize()} is not economically viable under current conditions. "
            f"Water generates ${shadow_price:.2f}/acre-ft value here vs "
            f"much higher returns in other crops. "
            f"Fallow this crop and redirect water (or sell your allocation if trading is available)."
        )

    # Use the breakeven calculation: buy if income/ET > lease price
    et_feet = WATER_DEPTH_FT[crop].get("dona_ana", 3.0)  # approximate
    breakeven = NET_REVENUE_PER_ACRE[crop].get("dona_ana", 500) / max(et_feet, 0.1)

    if shadow_price > lease_price * 1.15 and retention < 0.95:
        return "consider_buying_water", (
            f"Water is worth ${shadow_price:.2f}/acre-ft to your {crop} operation "
            f"vs ${lease_price:.2f}/acre-ft to lease. "
            f"Buying additional water is economically justified — "
            f"see the buy vs. fallow analysis below for exact quantities."
        )

    if retention >= 0.90:
        return "maintain", (
            f"{crop.capitalize()} is a high-value crop that maintains "
            f"{retention*100:.1f}% of acreage even under this shortage. "
            f"Prioritize water allocation here. "
            f"Income at risk: ${income_at_risk:,.0f}."
        )

    if retention >= 0.60:
        reduction_pct = (1 - retention) * 100
        return "reduce", (
            f"Reduce {crop} acreage by {reduction_pct:.0f}% "
            f"({(1-retention) * 100:.0f}% of your acres should be fallowed). "
            f"Focus remaining water on your highest-yielding fields. "
            f"Income at risk: ${income_at_risk:,.0f}."
        )

    return "reduce", (
        f"Significant reduction in {crop} acreage recommended — "
        f"only {retention*100:.0f}% of current acreage is viable. "
        f"Consider whether selling water rights generates more value than "
        f"maintaining reduced production. "
        f"Income at risk: ${income_at_risk:,.0f}."
    )


# ─────────────────────────────────────────────────────────────
# MAIN ORCHESTRATION FUNCTION
# ─────────────────────────────────────────────────────────────

def generate_recommendation(req: RecommendationRequest) -> RecommendationResponse:
    """
    Main entry point. Orchestrates all recommendation components.

    Flow:
    1. Optionally fetch live data (prices, ET, drought status)
    2. Build crop-level recommendations for chosen institution
    3. Rank all strategies (all three institutions)
    4. Calculate buy-vs-fallow for each crop
    5. Build headline recommendation
    6. Return complete response
    """
    county = req.county.value
    institution = req.trading_institution.value
    shortage_pct = req.shortage_pct

    # Determine lease price
    lease_price = req.current_lease_price or WATER_LEASE_PRICE_RANGE["mid"]

    # Fetch live data if requested
    live_prices = None
    live_et = None
    live_context = None

    if req.use_live_data:
        try:
            from services.external_data import get_live_context
            crop_names = [c.crop.lower() for c in req.crops]
            live_context = get_live_context(county, crop_names)
            live_prices = live_context.get("prices")
            live_et = live_context.get("et")
            print(f"Using live data for {county}: "
                  f"{len(live_prices or {})} prices, {len(live_et or {})} ET values")
        except Exception as e:
            print(f"Live data fetch failed, using paper values: {e}")

    # ── Step 1: Build crop-level recommendations ──────────────
    crop_recommendations = []
    total_baseline_income = 0.0
    total_drought_income = 0.0

    for crop_input in req.crops:
        crop = crop_input.crop.lower()
        user_acres = crop_input.acres

        rec = build_crop_recommendation(
            crop=crop,
            county=county,
            institution=institution,
            shortage_pct=shortage_pct,
            user_acres=user_acres,
            current_lease_price=lease_price,
            live_prices=live_prices,
            live_et=live_et,
        )
        crop_recommendations.append(rec)

        net_rev = (
            live_prices.get(crop) if live_prices and crop in live_prices
            else NET_REVENUE_PER_ACRE[crop][county]
        )
        total_baseline_income += user_acres * net_rev
        retention = interpolate_retention(crop, institution, county, shortage_pct)
        total_drought_income += user_acres * retention * net_rev

    # ── Step 2: Rank all strategies ───────────────────────────
    crops_list = [
        {"crop": c.crop.lower(), "acres": c.acres}
        for c in req.crops
    ]
    strategy_comparison = rank_strategies(
        county=county,
        crops=crops_list,
        shortage_pct=shortage_pct,
        current_lease_price=lease_price,
        live_prices=live_prices,
        live_et=live_et,
    )

    # ── Step 3: Buy vs fallow for each crop ───────────────────
    buy_vs_fallow = []
    for crop_input in req.crops:
        crop = crop_input.crop.lower()
        bvf = calculate_buy_vs_fallow(
            crop=crop,
            county=county,
            institution=institution,
            shortage_pct=shortage_pct,
            user_acres=crop_input.acres,
            current_lease_price=lease_price,
            live_prices=live_prices,
            live_et=live_et,
        )
        buy_vs_fallow.append(bvf)

    # ── Step 4: Sort crop recommendations ─────────────────────
    # Priority: maintain first, fallow last, buying water second
    action_order = {
        "maintain": 0,
        "consider_buying_water": 1,
        "reduce": 2,
        "fallow": 3,
    }
    crop_recommendations.sort(
        key=lambda x: action_order.get(x.action, 4)
    )

    # ── Step 5: Compute totals ─────────────────────────────────
    estimated_loss = total_baseline_income - total_drought_income
    preservation_pct = (
        (total_drought_income / total_baseline_income * 100)
        if total_baseline_income > 0 else 0
    )

    # ── Step 6: Build headline ─────────────────────────────────
    headline = _build_headline(
        shortage_pct=shortage_pct,
        institution=institution,
        preservation_pct=preservation_pct,
        estimated_loss=estimated_loss,
        crop_recommendations=crop_recommendations,
        strategy_comparison=strategy_comparison,
        lease_price=lease_price,
    )

    # ── Step 7: Build data source note ────────────────────────
    data_note = (
        "Recommendations calibrated to Ward et al. (2025) "
        "Agricultural Water Management and Ward (2025) "
        "Water Resources Management, Rio Grande Basin, New Mexico. "
    )
    if shortage_pct != 25.0:
        data_note += (
            f"Results interpolated/extrapolated from 25% shortage scenario "
            f"to your {shortage_pct:.0f}% input. "
        )
    if live_prices:
        data_note += "Crop prices updated with current USDA NASS data. "
    if live_et:
        data_note += "Water use (ET) updated with current OpenET satellite data. "
    data_note += "Use as decision-support guidance, not prescriptive advice."

    return RecommendationResponse(
        county=county,
        shortage_pct=shortage_pct,
        trading_institution=institution,
        total_baseline_income=round(total_baseline_income, 2),
        estimated_income_loss=round(estimated_loss, 2),
        income_preservation_pct=round(preservation_pct, 2),
        crop_recommendations=crop_recommendations,
        strategy_comparison=strategy_comparison,
        buy_vs_fallow=buy_vs_fallow,
        headline_recommendation=headline,
        data_source_note=data_note,
        live_data_used=bool(live_prices or live_et),
        live_context=live_context,
    )


def _build_headline(
    shortage_pct: float,
    institution: str,
    preservation_pct: float,
    estimated_loss: float,
    crop_recommendations: list,
    strategy_comparison: list,
    lease_price: float,
) -> str:
    """
    Builds the top-level summary sentence shown prominently in the UI.
    Designed to be readable at a glance without domain knowledge.
    """
    institution_plain = {
        "unlimited": "unrestricted water trading",
        "limited": "within-county water trading",
        "none": "proportional sharing (no trading)",
    }.get(institution, institution)

    parts = [
        f"Under a {shortage_pct:.0f}% water shortage with {institution_plain}, "
        f"you can preserve approximately {preservation_pct:.1f}% of your income "
        f"(estimated loss: ${estimated_loss:,.0f})."
    ]

    # Find better strategy if available
    current_loss = estimated_loss
    best_strategy = min(strategy_comparison, key=lambda x: x.estimated_income_loss_usd)
    if best_strategy.institution != institution:
        savings = current_loss - best_strategy.estimated_income_loss_usd
        if savings > 1000:
            better_name = {
                "unlimited": "unrestricted trading",
                "limited": "within-county trading",
            }.get(best_strategy.institution, best_strategy.institution)
            parts.append(
                f"Switching to {better_name} could save an additional "
                f"${savings:,.0f} in income losses."
            )

    # Highlight immediate actions
    fallow_crops = [r.crop for r in crop_recommendations if r.action == "fallow"]
    buy_crops = [r.crop for r in crop_recommendations if r.action == "consider_buying_water"]

    if fallow_crops:
        parts.append(f"Recommended to fallow: {', '.join(fallow_crops)}.")
    if buy_crops:
        parts.append(
            f"Buying water is economically justified for: {', '.join(buy_crops)} "
            f"(current lease rate: ${lease_price:.2f}/acre-ft)."
        )

    return " ".join(parts)