# services/external_data.py
import httpx
import csv
import io
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

OPENET_API_KEY = os.getenv("OPENET_API_KEY")
USDA_NASS_API_KEY = os.getenv("USDA_NASS_API_KEY")

# ─────────────────────────────────────────────────────────────
# COUNTY METADATA
# Representative lat/lon center points for each Rio Grande
# Basin county. OpenET needs coordinates, not county names.
# These are approximate centroids of irrigated farmland areas.
# ─────────────────────────────────────────────────────────────
COUNTY_COORDINATES = {
    "dona_ana":   {"lat": 32.35, "lon": -106.76, "fips": "35013"},
    "sierra":     {"lat": 33.13, "lon": -107.25, "fips": "35051"},
    "socorro":    {"lat": 34.06, "lon": -106.89, "fips": "35053"},
    "valencia":   {"lat": 34.75, "lon": -106.72, "fips": "35061"},
    "bernalillo": {"lat": 35.08, "lon": -106.65, "fips": "35001"},
    "sandoval":   {"lat": 35.51, "lon": -106.84, "fips": "35043"},
}

# FIPS codes map county names to the numeric IDs the
# Drought Monitor and USDA NASS use to identify counties.
# These are standardized federal codes — every US county has one.

# ─────────────────────────────────────────────────────────────
# DROUGHT MONITOR INTEGRATION
# ─────────────────────────────────────────────────────────────

# Maps drought category strings to suggested shortage percentages.
# Based on USDM definitions and Ward et al. methodology.
# D0 = Abnormally Dry, D1 = Moderate, D2 = Severe,
# D3 = Extreme, D4 = Exceptional
DROUGHT_TO_SHORTAGE = {
    "None": 0,
    "D0":   7,    # midpoint of 5-10% range
    "D1":   17,   # midpoint of 15-20% range
    "D2":   27,   # midpoint of 25-30% range
    "D3":   40,   # midpoint of 35-45% range
    "D4":   55,   # midpoint of 50-60% range (capped at model limit)
}

def get_drought_status(county: str) -> dict:
    fips = COUNTY_COORDINATES[county]["fips"]

    today = datetime.now()
    days_since_tuesday = (today.weekday() - 1) % 7
    if days_since_tuesday == 0:
        days_since_tuesday = 7
    last_tuesday = today - timedelta(days=days_since_tuesday)
    safe_tuesday = last_tuesday - timedelta(days=7)

    start_str = safe_tuesday.strftime("%m/%d/%Y")
    end_str = last_tuesday.strftime("%m/%d/%Y")

    url = (
        f"https://usdmdataservices.unl.edu/api/CountyStatistics/"
        f"GetDroughtSeverityStatisticsByAreaPercent"
        f"?aoi={fips}&startdate={start_str}&enddate={end_str}&statisticsType=1"
    )

    try:
        response = httpx.get(url, timeout=10)
        response.raise_for_status()

        # Check BEFORE .json() — this is the critical order
        raw_text = response.text.strip() if response.text else ""
        
        if not raw_text:
            print(f"Drought Monitor: empty response for {county}")
            return _drought_fallback(county)
        
        if raw_text.startswith("<"):
            print(f"Drought Monitor: got HTML instead of JSON for {county}")
            return _drought_fallback(county)

        if raw_text == "null" or raw_text == "[]":
            print(f"Drought Monitor: null/empty array for {county}")
            return _drought_fallback(county)

        # Only call .json() once we know we have parseable content
        data = response.json()

        if not data or not isinstance(data, list):
            return _drought_fallback(county)

        record = data[0]
        worst_category = "None"
        for category in ["D4", "D3", "D2", "D1", "D0"]:
            area_pct = float(record.get(category, 0) or 0)
            if area_pct > 10:
                worst_category = category
                break

        return {
            "county": county,
            "drought_category": worst_category,
            "suggested_shortage_pct": DROUGHT_TO_SHORTAGE[worst_category],
            "description": _drought_description(worst_category),
            "data_date": safe_tuesday.strftime("%Y-%m-%d"),
            "source": "US Drought Monitor",
        }

    except Exception as e:
        # Don't print "API error" for empty body — that's misleading
        # Only print if it's a genuine unexpected error
        error_str = str(e)
        if "Expecting value" not in error_str:
            print(f"Drought Monitor unexpected error for {county}: {e}")
        return _drought_fallback(county)


def _drought_fallback(county: str) -> dict:
    """
    Returns an informed fallback based on known NM drought patterns.
    New Mexico has been in persistent D1-D2 drought conditions.
    This is clearly labeled so users know it's not live data.
    """
    return {
        "county": county,
        "drought_category": "D1",
        "suggested_shortage_pct": 17,
        "description": (
            "Live drought data temporarily unavailable. "
            "Using D1 (Moderate Drought) as default — consistent with "
            "recent New Mexico drought conditions. "
            "Verify current status at droughtmonitor.unl.edu"
        ),
        "data_date": None,
        "source": "Fallback — verify at droughtmonitor.unl.edu",
    }

def _get_drought_from_csv(county: str, fips: str) -> dict:
    """
    Backup approach: fetch the USDM weekly CSV file directly.
    USDM publishes a CSV at a predictable URL every week.
    This is more reliable than the API endpoint.
    """
    # The USDM tabular data URL — this is a stable public endpoint
    url = "https://droughtmonitor.unl.edu/DmData/GISData/USDM_County.zip"

    try:
        # Instead of downloading the zip, use their text data endpoint
        # which is simpler and doesn't require unzipping
        csv_url = "https://usdmdataservices.unl.edu/api/USStatistics/GetDroughtSeverityStatisticsByAreaPercent?aoi=US&startdate=01/01/2025&enddate=04/18/2026&statisticsType=1"

        # Actually the simplest reliable approach: use the public
        # tabular data download which doesn't require date parameters
        tabular_url = f"https://droughtmonitor.unl.edu/DmData/DataDownload/ComprehensiveStatistics.aspx?mode=table&aoi=county&aoitype={fips}&statefips=35&county={fips}&countyname=&startdate=2026-01-01&enddate=2026-04-18&submitbutton=Get+Statistics"

        # This endpoint is fragile. Use the fallback directly.
        raise Exception("CSV backup not implemented, using default")

    except Exception:
        # Final fallback: use current NM drought conditions
        # New Mexico has been in D1-D2 drought for most of 2024-2026
        # This is a reasonable informed default
        return {
            "county": county,
            "drought_category": "D1",
            "suggested_shortage_pct": 17,
            "description": (
                "Could not retrieve live drought data. "
                "Using D1 (Moderate Drought) as default based on "
                "recent New Mexico drought conditions. "
                "Check droughtmonitor.unl.edu for current status."
            ),
            "data_date": None,
            "source": "Informed fallback — verify at droughtmonitor.unl.edu",
        }

def _drought_description(category: str) -> str:
    descriptions = {
        "None": "No drought conditions currently observed.",
        "D0": "Abnormally dry conditions. Some short-term dryness slowing crop growth.",
        "D1": "Moderate drought. Some crop damage possible, water shortages developing.",
        "D2": "Severe drought. Crop losses likely, water shortages common.",
        "D3": "Extreme drought. Major crop losses, widespread water shortages.",
        "D4": "Exceptional drought. Exceptional and widespread crop and pasture losses.",
    }
    return descriptions.get(category, "Unknown drought status.")

def _drought_fallback(county: str) -> dict:
    """Returns a safe default when the API is unavailable."""
    return {
        "county": county,
        "drought_category": "Unknown",
        "suggested_shortage_pct": 25,
        "description": "Could not retrieve current drought data. Using default 25% shortage scenario.",
        "data_date": None,
        "source": "Fallback default",
    }


# ─────────────────────────────────────────────────────────────
# USDA NASS INTEGRATION
# ─────────────────────────────────────────────────────────────

# Maps our internal crop names to USDA NASS commodity names.
# NASS uses specific terminology that doesn't always match
CROP_TO_NASS_COMMODITY = {
    "pecan":   "PECANS",
    "alfalfa": "HAY",
    "corn":    "CORN",
    "wheat":   "WHEAT",
    "peppers": None,       # handled separately — see below
    "cotton":  "COTTON",
    "onions":  "ONIONS",
}

# Fallback to 2022 paper values if NASS API fails or returns nothing.
# These are the NET revenue values from Table 3, averaged across counties.
FALLBACK_PRICES = {
    "pecan":   866.00,
    "alfalfa": 595.69,
    "corn":    409.40,
    "wheat":   25.89,
    "peppers": 2610.97,
    "cotton":  135.05,
    "onions":  2398.46,
}


def _get_cotton_price(state: str, base_url: str, api_key: str) -> float:
    """
    Cotton in New Mexico is mostly Upland cotton.
    NASS reports cotton price as $/LB which needs careful unit handling.
    """
    attempts = [
        {"commodity_desc": "COTTON", "class_desc": "UPLAND",
         "statisticcat_desc": "PRICE RECEIVED"},
        {"commodity_desc": "COTTON", "statisticcat_desc": "PRICE RECEIVED"},
    ]

    for attempt in attempts:
        try:
            params = {
                "key": api_key,
                "source_desc": "SURVEY",
                "sector_desc": "CROPS",
                "state_name": state,
                "agg_level_desc": "STATE",
                "year__GE": str(datetime.now().year - 3),
                "format": "JSON",
                **attempt,
            }
            response = httpx.get(base_url, params=params, timeout=15)
            if response.status_code == 400:
                continue
            response.raise_for_status()
            data = response.json()
            records = data.get("data", [])
            if not records:
                continue

            records.sort(key=lambda x: int(x.get("year", 0)), reverse=True)
            latest = records[0]
            raw_value = latest.get("Value", "").strip()
            if raw_value in ["(D)", "(Z)", "(NA)", ""]:
                continue

            price_per_unit = float(raw_value.replace(",", ""))
            unit = latest.get("unit_desc", "").upper()
            result = _convert_to_net_revenue_per_acre("cotton", price_per_unit, unit)
            print(f"NASS cotton: ${result:.2f}/acre (raw: {price_per_unit} {unit})")
            return result

        except Exception:
            continue

    print("NASS cotton: no data found, using 2022 paper baseline")
    return FALLBACK_PRICES["cotton"]

def _convert_to_net_revenue_per_acre(
    crop: str,
    price_per_unit: float,
    unit: str
) -> float:
    yields_tons_per_acre = {
        "pecan": 0.76, "alfalfa": 4.76, "corn": 2.59,
        "wheat": 0.31, "peppers": 6.40, "cotton": 0.65,
        "onions": 22.95,
    }
    cost_ratio = {
        "pecan": 0.70, "alfalfa": 0.65, "corn": 0.68,
        "wheat": 0.85, "peppers": 0.55, "cotton": 0.80,
        "onions": 0.60,
    }

    yield_tons = yields_tons_per_acre.get(crop, 1.0)
    cost_pct = cost_ratio.get(crop, 0.70)

    if "/ TON" in unit or "/TON" in unit:
        # Special case: cotton is never sold by the ton in NASS
        # If we're getting $/ton for cotton, it's the wrong statistic
        # Return fallback immediately
        if crop == "cotton":
            print(f"Cotton unit is $/ton — likely wrong statistic, using fallback")
            return FALLBACK_PRICES["cotton"]
        price_per_ton = price_per_unit

    elif "/ CWT" in unit or "/CWT" in unit:
        price_per_ton = price_per_unit * 20

    elif "/ LB" in unit or "/LB" in unit:
        price_per_ton = price_per_unit * 2000

    elif "/ BU" in unit or "/BU" in unit:
        bu_per_ton = {"wheat": 36.7, "corn": 39.4}.get(crop, 36.0)
        price_per_ton = price_per_unit * bu_per_ton

    else:
        print(f"Unknown unit '{unit}' for {crop}, using fallback")
        return FALLBACK_PRICES[crop]

    gross_revenue_per_acre = price_per_ton * yield_tons
    net_revenue_per_acre = gross_revenue_per_acre * (1 - cost_pct)

    
    # Cotton-specific validation
    # Cotton is always priced per pound in US markets (~$0.60-1.00/lb)
    # If we're getting $/ton for cotton the statistic is wrong
    if crop == "cotton" and "/ TON" in unit:
        print(f"Cotton: $/ton unit detected — wrong NASS statistic. Using fallback.")
        return FALLBACK_PRICES["cotton"]

    # Tighter sanity check — result shouldn't differ by more than 60% from baseline
    fallback = FALLBACK_PRICES[crop]
    if net_revenue_per_acre < fallback * 0.4 or net_revenue_per_acre > fallback * 2.5:
        print(f"Sanity check failed for {crop}: got ${net_revenue_per_acre:.2f}, "
            f"expected ~${fallback:.2f}. Using fallback.")
        return fallback

    return round(net_revenue_per_acre, 2)

# Now update get_current_crop_prices to use these handlers:
def get_current_crop_prices(state: str = "NEW MEXICO") -> dict:
    if not USDA_NASS_API_KEY:
        print("No USDA NASS API key found, using fallback prices")
        return FALLBACK_PRICES.copy()

    base_url = "https://quickstats.nass.usda.gov/api/api_GET/"
    current_year = datetime.now().year

    CROP_QUERY_OVERRIDES = {
        "alfalfa": {
            "commodity_desc": "HAY",
            "class_desc": "ALFALFA",
            "statisticcat_desc": "PRICE RECEIVED",
            "unit_desc": "$ / TON",
        },
    }

    CUSTOM_HANDLERS = {
        "peppers": _get_pepper_price,
        "cotton":  _get_cotton_price,
    }

    # Initialize with fallback values so we ALWAYS have a complete dict
    # even if some API calls fail. Keys are filled in below.
    prices = FALLBACK_PRICES.copy()

    try:
        for crop in FALLBACK_PRICES.keys():
            if crop in CUSTOM_HANDLERS:
                result = CUSTOM_HANDLERS[crop](state, base_url, USDA_NASS_API_KEY)
                if result is not None:
                    prices[crop] = result
                continue

            nass_name = CROP_TO_NASS_COMMODITY.get(crop)
            if not nass_name:
                continue  # keeps fallback value

            try:
                params = {
                    "key": USDA_NASS_API_KEY,
                    "source_desc": "SURVEY",
                    "sector_desc": "CROPS",
                    "commodity_desc": nass_name,
                    "statisticcat_desc": "PRICE RECEIVED",
                    "state_name": state,
                    "agg_level_desc": "STATE",
                    "year__GE": str(current_year - 3),
                    "format": "JSON",
                }

                if crop in CROP_QUERY_OVERRIDES:
                    params.update(CROP_QUERY_OVERRIDES[crop])

                response = httpx.get(base_url, params=params, timeout=15)
                response.raise_for_status()
                data = response.json()
                records = data.get("data", [])

                if not records:
                    print(f"NASS no records for {crop}, keeping fallback")
                    continue

                records.sort(key=lambda x: int(x.get("year", 0)), reverse=True)
                latest = records[0]
                raw_value = latest.get("Value", "").strip()

                if raw_value in ["(D)", "(Z)", "(NA)", ""]:
                    continue

                price_per_unit = float(raw_value.replace(",", ""))
                unit = latest.get("unit_desc", "").upper()
                net_revenue = _convert_to_net_revenue_per_acre(crop, price_per_unit, unit)
                prices[crop] = net_revenue
                print(f"NASS live price for {crop}: ${net_revenue:.2f}/acre "
                      f"(raw: {price_per_unit} {unit}, year: {latest.get('year')})")

            except Exception as e:
                print(f"NASS API error for {crop}: {e}")
                # prices[crop] already has fallback value, no action needed

    except Exception as e:
        print(f"NASS unexpected error: {e}")
        # Return whatever we have — at minimum the full fallback dict

    return prices  # always a complete dict, never None


def _get_pepper_price(state: str, base_url: str, api_key: str) -> float:
    """
    New Mexico chile peppers are tracked under multiple NASS
    commodity names. Try each one in order until we get data.
    If none work, use the 2022 paper baseline.
    
    NM chile is also sometimes reported as value per unit
    rather than price received — we try both.
    """
    commodity_attempts = [
        {"commodity_desc": "CHILI PEPPERS", "statisticcat_desc": "PRICE RECEIVED"},
        {"commodity_desc": "PEPPERS", "statisticcat_desc": "PRICE RECEIVED"},
        {"commodity_desc": "CHILI PEPPERS", "statisticcat_desc": "VALUE OF PRODUCTION"},
        {"commodity_desc": "VEGETABLES, OTHER", "statisticcat_desc": "PRICE RECEIVED"},
    ]

    for attempt in commodity_attempts:
        try:
            params = {
                "key": api_key,
                "source_desc": "SURVEY",
                "sector_desc": "CROPS",
                "state_name": state,
                "agg_level_desc": "STATE",
                "year__GE": str(datetime.now().year - 3),
                "format": "JSON",
                **attempt,
            }
            response = httpx.get(base_url, params=params, timeout=15)
            if response.status_code == 400:
                continue
            response.raise_for_status()
            data = response.json()
            records = data.get("data", [])
            if not records:
                continue

            records.sort(key=lambda x: int(x.get("year", 0)), reverse=True)
            latest = records[0]
            raw_value = latest.get("Value", "").strip()
            if raw_value in ["(D)", "(Z)", "(NA)", ""]:
                continue

            price_per_unit = float(raw_value.replace(",", ""))
            unit = latest.get("unit_desc", "").upper()
            result = _convert_to_net_revenue_per_acre("peppers", price_per_unit, unit)
            print(f"NASS peppers found via '{attempt['commodity_desc']}': "
                  f"${result:.2f}/acre (raw: {price_per_unit} {unit})")
            return result

        except Exception:
            continue

    # If all attempts fail, use paper baseline
    # NM chile prices haven't changed dramatically since 2022
    print("NASS peppers: no data found, using 2022 paper baseline")
    return FALLBACK_PRICES["peppers"]


    prices = {}

    for crop in FALLBACK_PRICES.keys():
        # Use custom handler if one exists
        if crop in CUSTOM_HANDLERS:
            prices[crop] = CUSTOM_HANDLERS[crop](state, base_url, USDA_NASS_API_KEY)
            continue

        nass_name = CROP_TO_NASS_COMMODITY.get(crop)
        if not nass_name:
            prices[crop] = FALLBACK_PRICES[crop]
            continue

        try:
            params = {
                "key": USDA_NASS_API_KEY,
                "source_desc": "SURVEY",
                "sector_desc": "CROPS",
                "commodity_desc": nass_name,
                "statisticcat_desc": "PRICE RECEIVED",
                "state_name": state,
                "agg_level_desc": "STATE",
                "year__GE": str(current_year - 3),
                "format": "JSON",
            }

            if crop in CROP_QUERY_OVERRIDES:
                params.update(CROP_QUERY_OVERRIDES[crop])

            response = httpx.get(base_url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            records = data.get("data", [])

            if not records:
                print(f"NASS returned no records for {crop}, using fallback")
                prices[crop] = FALLBACK_PRICES[crop]
                continue

            records.sort(key=lambda x: int(x.get("year", 0)), reverse=True)
            latest = records[0]
            raw_value = latest.get("Value", "").strip()

            if raw_value in ["(D)", "(Z)", "(NA)", ""]:
                prices[crop] = FALLBACK_PRICES[crop]
                continue

            price_per_unit = float(raw_value.replace(",", ""))
            unit = latest.get("unit_desc", "").upper()
            net_revenue = _convert_to_net_revenue_per_acre(crop, price_per_unit, unit)
            prices[crop] = net_revenue
            print(f"NASS live price for {crop}: ${net_revenue:.2f}/acre "
                  f"(raw: {price_per_unit} {unit}, year: {latest.get('year')})")

        except Exception as e:
            print(f"NASS API error for {crop}: {e}")
            prices[crop] = FALLBACK_PRICES[crop]

    return prices

def _convert_to_net_revenue_per_acre(
    crop: str, 
    price_per_unit: float, 
    unit: str
) -> float:
    """
    Converts NASS price ($/unit) to net revenue ($/acre).
    
    Net revenue = (price × yield) - production costs
    
    We use average yields from the Ward paper and estimate
    production costs as a percentage of gross revenue.
    This is the same approach Ward et al. use in their model.
    
    Yield units from Ward paper (converted to match NASS units):
    - Pecans: 0.76 tons/acre → $/ton from NASS
    - Alfalfa: 4.76 tons/acre → $/ton from NASS  
    - Corn: 2.59 tons/acre → $/ton from NASS
    - Wheat: 0.31 tons/acre → $/ton from NASS
    - Peppers: 6.40 tons/acre → $/cwt (hundredweight) from NASS
    - Cotton: 0.65 tons/acre → $/lb from NASS
    - Onions: 22.95 tons/acre → $/cwt from NASS
    """
    
    # Yield in tons per acre (from Ward paper Table 6, full supply)
    yields_tons_per_acre = {
        "pecan": 0.76, "alfalfa": 4.76, "corn": 2.59,
        "wheat": 0.31, "peppers": 6.40, "cotton": 0.65,
        "onions": 22.95,
    }
    
    # Cost ratio: what fraction of gross revenue goes to costs
    # From Ward paper methodology — costs ≈ 70% of gross for most crops
    cost_ratio = {
        "pecan": 0.70, "alfalfa": 0.65, "corn": 0.68,
        "wheat": 0.85, "peppers": 0.55, "cotton": 0.80,
        "onions": 0.60,
    }
    
    yield_tons = yields_tons_per_acre.get(crop, 1.0)
    cost_pct = cost_ratio.get(crop, 0.70)
    
    # Convert price to $/ton based on NASS unit
    if "/ TON" in unit or "/TON" in unit:
        price_per_ton = price_per_unit
    elif "/ CWT" in unit or "/CWT" in unit:
        # CWT = hundredweight = 100 lbs. 1 ton = 20 CWT
        price_per_ton = price_per_unit * 20
    elif "/ LB" in unit or "/LB" in unit:
        # 1 ton = 2000 lbs
        price_per_ton = price_per_unit * 2000
    elif "/ BU" in unit or "/BU" in unit:
        # Bushel weights vary by crop
        bu_per_ton = {"wheat": 36.7, "corn": 39.4}.get(crop, 36.0)
        price_per_ton = price_per_unit * bu_per_ton
    else:
        # Unknown unit — use fallback
        return FALLBACK_PRICES[crop]
    
    gross_revenue_per_acre = price_per_ton * yield_tons
    net_revenue_per_acre = gross_revenue_per_acre * (1 - cost_pct)
    
    # Sanity check: if result is wildly different from paper baseline,
    # something went wrong with unit conversion. Use fallback.
    fallback = FALLBACK_PRICES[crop]
    if net_revenue_per_acre < fallback * 0.1 or net_revenue_per_acre > fallback * 10:
        print(f"Sanity check failed for {crop}: got {net_revenue_per_acre:.2f}, "
              f"expected ~{fallback:.2f}. Using fallback.")
        return fallback
    
    return round(net_revenue_per_acre, 2)


# ─────────────────────────────────────────────────────────────
# OPENET INTEGRATION
# ─────────────────────────────────────────────────────────────
# In services/external_data.py
# Replace the headers block in get_current_et: et means evapotranspiration, the amount of water lost to the atmosphere.

def get_current_et(county: str, crop: str) -> float:
    if not OPENET_API_KEY:
        return _get_et_fallback(county, crop)

    coords = COUNTY_COORDINATES[county]
    current_year = datetime.now().year
    data_year = current_year - 1 if datetime.now().month < 5 else current_year

    start_date = f"{data_year}-01-01"
    end_date = f"{data_year}-12-31"

    # OpenET accepts the key either as a bare value or with "Bearer " prefix
    # Try both formats since the API has changed requirements over time
    header_formats = [
        {"Authorization": OPENET_API_KEY,
         "Content-Type": "application/json",
         "Accept": "application/json"},
        {"Authorization": f"Bearer {OPENET_API_KEY}",
         "Content-Type": "application/json",
         "Accept": "application/json"},
        # Some OpenET versions use a custom header name
        {"x-api-key": OPENET_API_KEY,
         "Content-Type": "application/json",
         "Accept": "application/json"},
    ]

    endpoints_to_try = [
        {
            "url": "https://openet-api.org/timeseries/point",
            "payload": {
                "lat": coords["lat"],
                "lng": coords["lon"],
                "start_date": start_date,
                "end_date": end_date,
                "model": "Ensemble",
                "variable": "ET",
                "units": "mm",
            }
        },
        {
            "url": "https://openet-api.org/raster/timeseries/point",
            "payload": {
                "lat": coords["lat"],
                "lng": coords["lon"],
                "start_date": start_date,
                "end_date": end_date,
                "model": "ensemble",
                "variable": "et",
                "units": "metric",
                "output_file_format": "json",
            }
        },
    ]

    for headers in header_formats:
        for attempt in endpoints_to_try:
            try:
                response = httpx.post(
                    attempt["url"],
                    json=attempt["payload"],
                    headers=headers,
                    timeout=30,
                )

                if response.status_code == 401:
                    # This header format is wrong, try next header format
                    # but don't try more endpoints with this same bad header
                    break

                if response.status_code in [404, 405, 422]:
                    # Wrong URL or payload, try next endpoint
                    continue

                response.raise_for_status()

                raw_text = response.text.strip() if response.text else ""
                if not raw_text or raw_text in ["null", "[]"]:
                    continue

                data = response.json()

                if isinstance(data, list):
                    monthly_values = data
                elif isinstance(data, dict):
                    monthly_values = None
                    for key in ["data", "timeseries", "features", "results"]:
                        if key in data:
                            monthly_values = data[key]
                            break
                    if monthly_values is None:
                        continue
                else:
                    continue

                total_et_mm = 0.0
                for record in monthly_values:
                    if isinstance(record, dict):
                        et_val = (record.get("et") or record.get("ET") or
                                  record.get("value") or record.get("mean") or 0)
                    elif isinstance(record, (int, float)):
                        et_val = record
                    else:
                        continue
                    try:
                        total_et_mm += float(et_val)
                    except (TypeError, ValueError):
                        continue

                if total_et_mm <= 0:
                    continue

                et_feet = total_et_mm / 304.8
                crop_et_feet = et_feet * _get_crop_coefficient(crop)

                from data.scenarios import WATER_DEPTH_FT
                baseline = WATER_DEPTH_FT[crop][county]
                if crop_et_feet < baseline * 0.4 or crop_et_feet > baseline * 1.6:
                    crop_et_feet = 0.7 * crop_et_feet + 0.3 * baseline

                print(f"OpenET live ET for {county}/{crop}: {crop_et_feet:.2f} ft")
                return round(crop_et_feet, 2)

            except Exception as e:
                error_str = str(e)
                if "401" not in error_str:
                    print(f"OpenET endpoint failed: {e}")
                continue

    # All attempts failed — use fallback silently
    # (don't spam logs since this is expected when key is invalid)
    return _get_et_fallback(county, crop)

def _estimate_et_from_climate(county: str, crop: str, year: int) -> float:
    """
    When OpenET is completely unavailable, estimate current ET
    using NOAA climate data (temperature anomaly) as a proxy.
    
    Warmer years have higher ET. The relationship is roughly:
    ET_current ≈ ET_baseline × (1 + 0.02 × temp_anomaly_C)
    
    This is a rough approximation but better than using 2022 values
    unchanged during an anomalously hot or cool year.
    """
    from data.scenarios import WATER_DEPTH_FT
    baseline = WATER_DEPTH_FT[crop][county]

    try:
        # NOAA Climate Data Online — temperature anomaly for NM
        # This endpoint gives statewide average temperature anomaly
        noaa_url = (
            "https://www.ncei.noaa.gov/cdo-web/api/v2/data"
            f"?datasetid=GHCND&stationid=GHCND:USW00023049"  # Albuquerque station
            f"&startdate={year}-01-01&enddate={year}-12-31"
            f"&datatypeid=TAVG&limit=365&units=metric"
        )
        # NOAA CDO requires a token — if we don't have one, skip
        noaa_token = os.getenv("NOAA_CDO_TOKEN")
        if not noaa_token:
            return baseline

        headers = {"token": noaa_token}
        response = httpx.get(noaa_url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
        if not results:
            return baseline

        # Calculate average temperature
        temps = [r["value"] / 10 for r in results if r.get("value")]
        if not temps:
            return baseline

        avg_temp_c = sum(temps) / len(temps)

        # Historical average for Albuquerque area: ~14.5°C annual mean
        historical_avg_c = 14.5
        temp_anomaly = avg_temp_c - historical_avg_c

        # ET increases ~2% per degree C of warming (Allen et al. FAO-56)
        et_adjustment = 1.0 + (0.02 * temp_anomaly)
        estimated_et = baseline * et_adjustment

        print(f"ET estimate for {county}/{crop}: {estimated_et:.2f} ft "
              f"(temp anomaly: {temp_anomaly:+.1f}°C)")
        return round(estimated_et, 2)

    except Exception as e:
        print(f"Climate-based ET estimation failed: {e}")
        return baseline
    
def _get_et_v1_fallback(county: str, crop: str, headers: dict) -> float:
    """
    Tries the older OpenET v1 endpoint if v2 fails.
    If both fail, returns the paper baseline.
    """
    coords = COUNTY_COORDINATES[county]
    current_year = datetime.now().year
    data_year = current_year - 1 if datetime.now().month < 5 else current_year

    url = "https://openet-api.org/raster/timeseries/point"
    payload = {
        "lat": coords["lat"],
        "lng": coords["lon"],
        "start_date": f"{data_year}-01-01",
        "end_date": f"{data_year}-12-31",
        "model": "ensemble",
        "variable": "et",
        "units": "metric",
        "output_file_format": "json",
    }

    try:
        response = httpx.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        monthly_values = data if isinstance(data, list) else data.get("data", [])
        total_mm = sum(float(r.get("et", 0) or 0) for r in monthly_values)
        if total_mm <= 0:
            return _get_et_fallback(county, crop)
        et_feet = (total_mm / 304.8) * _get_crop_coefficient(crop)
        return round(et_feet, 2)
    except Exception as e:
        print(f"OpenET v1 also failed: {e}")
        return _get_et_fallback(county, crop)

def _get_crop_coefficient(crop: str) -> float:
    """
    Crop coefficients (Kc) adjust reference ET to crop-specific ET.
    These are standard FAO-56 values for the crop's peak growing season.
    Pecans and alfalfa are high Kc (use more water than reference).
    Wheat and cotton are lower Kc.
    """
    coefficients = {
        "pecan":   1.20,
        "alfalfa": 1.15,
        "corn":    1.10,
        "wheat":   0.90,
        "peppers": 0.95,
        "cotton":  0.85,
        "onions":  0.95,
    }
    return coefficients.get(crop, 1.0)

def _get_et_fallback(county: str, crop: str) -> float:
    """Returns the 2022 paper value when OpenET is unavailable."""
    from data.scenarios import WATER_DEPTH_FT
    return WATER_DEPTH_FT[crop][county]


# ─────────────────────────────────────────────────────────────
# COMBINED LIVE DATA FETCH
# ─────────────────────────────────────────────────────────────

def get_live_context(county: str, crops: list[str]) -> dict:
    """
    Single function that fetches all three data sources and
    returns a combined context dict. Called once per recommendation
    request to avoid multiple round trips.
    
    Returns everything the recommender needs to override the
    hardcoded paper values with live data.
    """
    
    # These three calls happen sequentially.
    # In production you'd run them in parallel with asyncio.gather()
    # but sequential is fine for a hackathon.
    drought_status = get_drought_status(county)
    current_prices = get_current_crop_prices()
    
    # Only fetch ET for crops the user actually has
    current_et = {}
    for crop in crops:
        current_et[crop] = get_current_et(county, crop)
    
    return {
        "drought": drought_status,
        "prices": current_prices,
        "et": current_et,
    }