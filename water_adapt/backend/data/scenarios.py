# data/scenarios.py
# Encoded from Ward et al. (2025) Agricultural Water Management
# and Ward (2025) Water Resources Management

# Table 3: Net revenue per acre by crop and county ($/acre)
NET_REVENUE_PER_ACRE = {
    "pecan":   {"dona_ana": 866.00, "sierra": 838.52, "socorro": 803.84,
                "valencia": 510.37, "bernalillo": 620.67, "sandoval": 571.47},
    "alfalfa": {"dona_ana": 595.69, "sierra": 568.37, "socorro": 488.58,
                "valencia": 483.43, "bernalillo": 457.41, "sandoval": 458.43},
    "corn":    {"dona_ana": 409.40, "sierra": 400.18, "socorro": 389.60,
                "valencia": 324.51, "bernalillo": 307.19, "sandoval": 290.18},
    "wheat":   {"dona_ana": 25.89,  "sierra": 32.03,  "socorro": 11.55,
                "valencia": 24.91,  "bernalillo": 26.58, "sandoval": 11.56},
    "peppers": {"dona_ana": 2610.97,"sierra": 2496.00, "socorro": 2143.21,
                "valencia": 2097.33,"bernalillo": 2096.69,"sandoval": 2069.06},
    "cotton":  {"dona_ana": 135.05, "sierra": 70.52,  "socorro": 69.61,
                "valencia": 52.07,  "bernalillo": 67.53, "sandoval": 62.15},
    "onions":  {"dona_ana": 2398.46,"sierra": 2259.57, "socorro": 2014.24,
                "valencia": 1943.53,"bernalillo": 1886.76,"sandoval": 1809.77},
}

# Table 2: Water depth (ET) by crop and county (feet/acre/year)
WATER_DEPTH_FT = {
    "pecan":   {"dona_ana": 4.50, "sierra": 4.00, "socorro": 3.75,
                "valencia": 3.58, "bernalillo": 3.51, "sandoval": 3.40},
    "alfalfa": {"dona_ana": 3.42, "sierra": 3.17, "socorro": 2.83,
                "valencia": 2.75, "bernalillo": 2.67, "sandoval": 2.58},
    "corn":    {"dona_ana": 2.92, "sierra": 2.83, "socorro": 2.50,
                "valencia": 2.33, "bernalillo": 2.28, "sandoval": 2.17},
    "wheat":   {"dona_ana": 3.67, "sierra": 3.50, "socorro": 3.33,
                "valencia": 3.00, "bernalillo": 2.86, "sandoval": 2.77},
    "peppers": {"dona_ana": 2.83, "sierra": 2.67, "socorro": 2.33,
                "valencia": 2.28, "bernalillo": 2.21, "sandoval": 2.14},
    "cotton":  {"dona_ana": 2.50, "sierra": 2.33, "socorro": 2.07,
                "valencia": 2.01, "bernalillo": 1.95, "sandoval": 1.89},
    "onions":  {"dona_ana": 3.00, "sierra": 2.83, "socorro": 2.49,
                "valencia": 2.41, "bernalillo": 2.34, "sandoval": 2.27},
}

# Table 1: Observed baseline acres by crop and county
BASELINE_ACRES = {
    "pecan":   {"dona_ana": 39372, "sierra": 977,  "socorro": 426,
                "valencia": 731,   "bernalillo": 78, "sandoval": 62},
    "alfalfa": {"dona_ana": 13074, "sierra": 2052, "socorro": 9052,
                "valencia": 7011,  "bernalillo": 518, "sandoval": 1294},
    "corn":    {"dona_ana": 662,   "sierra": 502,  "socorro": 463,
                "valencia": 341,   "bernalillo": 19, "sandoval": 56},
    "wheat":   {"dona_ana": 1251,  "sierra": 576,  "socorro": 151,
                "valencia": 153,   "bernalillo": 35, "sandoval": 66},
    "peppers": {"dona_ana": 1498,  "sierra": 572,  "socorro": 213,
                "valencia": 11,    "bernalillo": 2,  "sandoval": 17},
    "cotton":  {"dona_ana": 14283, "sierra": 899,  "socorro": 265,
                "valencia": 46,    "bernalillo": 6,  "sandoval": 8},
    "onions":  {"dona_ana": 1989,  "sierra": 568,  "socorro": 133,
                "valencia": 188,   "bernalillo": 6,  "sandoval": 12},
}

# Table 4: Land retention proportion under 25% drought by institution
# proportion = optimized_drought_acres / full_supply_acres
LAND_RETENTION_DROUGHT_25PCT = {
    "unlimited": {
        "pecan":   {"dona_ana": 0.822, "sierra": 0.836, "socorro": 0.840,
                    "valencia": 0.759, "bernalillo": 0.806, "sandoval": 0.796},
        "alfalfa": {"dona_ana": 0.803, "sierra": 0.809, "socorro": 0.801,
                    "valencia": 0.805, "bernalillo": 0.800, "sandoval": 0.807},
        "corn":    {"dona_ana": 0.755, "sierra": 0.757, "socorro": 0.780,
                    "valencia": 0.753, "bernalillo": 0.746, "sandoval": 0.744},
        "wheat":   {"dona_ana": 0.000, "sierra": 0.000, "socorro": 0.000,
                    "valencia": 0.000, "bernalillo": 0.000, "sandoval": 0.000},
        "peppers": {"dona_ana": 0.963, "sierra": 0.963, "socorro": 0.963,
                    "valencia": 0.963, "bernalillo": 0.964, "sandoval": 0.964},
        "cotton":  {"dona_ana": 0.364, "sierra": 0.000, "socorro": 0.000,
                    "valencia": 0.000, "bernalillo": 0.008, "sandoval": 0.000},
        "onions":  {"dona_ana": 0.957, "sierra": 0.957, "socorro": 0.958,
                    "valencia": 0.957, "bernalillo": 0.957, "sandoval": 0.957},
    },
    "limited": {
        "pecan":   {"dona_ana": 0.822, "sierra": 0.905, "socorro": 0.815,
                    "valencia": 0.719, "bernalillo": 0.803, "sandoval": 0.778},
        "alfalfa": {"dona_ana": 0.803, "sierra": 0.889, "socorro": 0.770,
                    "valencia": 0.772, "bernalillo": 0.797, "sandoval": 0.790},
        "corn":    {"dona_ana": 0.755, "sierra": 0.859, "socorro": 0.746,
                    "valencia": 0.712, "bernalillo": 0.742, "sandoval": 0.721},
        "wheat":   {"dona_ana": 0.000, "sierra": 0.000, "socorro": 0.000,
                    "valencia": 0.000, "bernalillo": 0.000, "sandoval": 0.000},
        "peppers": {"dona_ana": 0.963, "sierra": 0.979, "socorro": 0.957,
                    "valencia": 0.956, "bernalillo": 0.963, "sandoval": 0.961},
        "cotton":  {"dona_ana": 0.364, "sierra": 0.339, "socorro": 0.000,
                    "valencia": 0.000, "bernalillo": 0.000, "sandoval": 0.000},
        "onions":  {"dona_ana": 0.957, "sierra": 0.975, "socorro": 0.951,
                    "valencia": 0.950, "bernalillo": 0.957, "sandoval": 0.953},
    },
    "none": {
        # Proportional sharing: all crops get exactly 0.75 of full supply
        "pecan":   {c: 0.75 for c in ["dona_ana","sierra","socorro","valencia","bernalillo","sandoval"]},
        "alfalfa": {c: 0.75 for c in ["dona_ana","sierra","socorro","valencia","bernalillo","sandoval"]},
        "corn":    {c: 0.75 for c in ["dona_ana","sierra","socorro","valencia","bernalillo","sandoval"]},
        "wheat":   {c: 0.75 for c in ["dona_ana","sierra","socorro","valencia","bernalillo","sandoval"]},
        "peppers": {c: 0.75 for c in ["dona_ana","sierra","socorro","valencia","bernalillo","sandoval"]},
        "cotton":  {c: 0.75 for c in ["dona_ana","sierra","socorro","valencia","bernalillo","sandoval"]},
        "onions":  {c: 0.75 for c in ["dona_ana","sierra","socorro","valencia","bernalillo","sandoval"]},
    }
}

# Table 7 (AWM paper): Shadow prices $/acre-ft under 25% drought
SHADOW_PRICES_DROUGHT_25PCT = {
    "unlimited": {
        # All crops and counties equalize at ~$68.67
        crop: {county: 68.67
               for county in ["dona_ana","sierra","socorro","valencia","bernalillo","sandoval"]}
        for crop in ["pecan","alfalfa","corn","wheat","peppers","cotton","onions"]
    },
    "limited": {
        # Equalizes within county, differs across counties
        "pecan":   {"dona_ana": 68.66, "sierra": 39.92, "socorro": 79.20,
                    "valencia": 80.07, "bernalillo": 69.59, "sandoval": 74.60},
        "alfalfa": {"dona_ana": 68.66, "sierra": 39.92, "socorro": 79.20,
                    "valencia": 80.07, "bernalillo": 69.59, "sandoval": 74.60},
        "corn":    {"dona_ana": 68.66, "sierra": 39.92, "socorro": 79.20,
                    "valencia": 80.07, "bernalillo": 69.59, "sandoval": 74.60},
        "wheat":   {"dona_ana": 68.66, "sierra": 39.92, "socorro": 79.20,
                    "valencia": 80.07, "bernalillo": 69.59, "sandoval": 74.60},
        "peppers": {"dona_ana": 68.66, "sierra": 39.92, "socorro": 79.20,
                    "valencia": 80.07, "bernalillo": 69.59, "sandoval": 74.60},
        "cotton":  {"dona_ana": 68.66, "sierra": 39.92, "socorro": 79.20,
                    "valencia": 80.07, "bernalillo": 69.59, "sandoval": 74.60},
        "onions":  {"dona_ana": 68.66, "sierra": 39.92, "socorro": 79.20,
                    "valencia": 80.07, "bernalillo": 69.59, "sandoval": 74.60},
    },
    "none": {
        "pecan":   {"dona_ana": 96.22, "sierra": 104.81,"socorro": 107.18,
                    "valencia": 71.21, "bernalillo": 88.36, "sandoval": 83.98},
        "alfalfa": {"dona_ana": 87.17, "sierra": 89.74, "socorro": 86.22,
                    "valencia": 87.90, "bernalillo": 85.76, "sandoval": 88.73},
        "corn":    {"dona_ana": 70.18, "sierra": 70.62, "socorro": 77.92,
                    "valencia": 69.54, "bernalillo": 67.47, "sandoval": 66.96},
        "wheat":   {"dona_ana": 3.53,  "sierra": 4.58,  "socorro": 1.73,
                    "valencia": 4.15,  "bernalillo": 4.64, "sandoval": 2.09},
        "peppers": {"dona_ana": 460.76,"sierra": 468.00, "socorro": 459.26,
                    "valencia": 459.84,"bernalillo": 474.07,"sandoval": 482.91},
        "cotton":  {"dona_ana": 27.01, "sierra": 15.11, "socorro": 16.79,
                    "valencia": 12.94, "bernalillo": 17.31, "sandoval": 16.44},
        "onions":  {"dona_ana": 399.74,"sierra": 398.75, "socorro": 404.82,
                    "valencia": 402.45,"bernalillo": 402.90,"sandoval": 398.93},
    }
}

# Income preservation by institution at 25% shortage (from Table 7 AWM paper)
INCOME_PRESERVATION = {
    "unlimited": 0.9591,
    "limited":   0.9586,
    "none":      0.9375,
}

# Total baseline income for study area (from Table 7)
TOTAL_BASELINE_INCOME_USD = 68_745_986

# Water lease price range for Rio Grande Basin (from literature)
# Used for buy vs. fallow calculator
WATER_LEASE_PRICE_RANGE = {
    "low": 43.88,   # 2017 interdistrict equilibrium (Table 7, WRM paper)
    "mid": 58.14,   # 2017 intradistrict EBID
    "high": 74.51,  # 2021 intradistrict EBID
}