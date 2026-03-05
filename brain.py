# Umbrella — Backend Brain
# This is where Umbrella's intelligence lives

import urllib.request
import json
import ssl
import certifi


# =============================================
# RAINFALL RISK CALCULATOR
# =============================================

def get_rainfall_risk(mm_48hr):
    if mm_48hr >= 115:
        return "HIGH"
    if mm_48hr >= 65:
        return "MEDIUM"
    return "LOW"


# =============================================
# FETCH LIVE RAINFALL FROM OPEN-METEO API
# =============================================

def fetch_rainfall(lat, lng):
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}"
        f"&longitude={lng}"
        f"&daily=precipitation_sum"
        f"&past_days=2"
        f"&forecast_days=1"
        f"&timezone=Asia%2FKolkata"
    )

    try:
        context = ssl.create_default_context(cafile=certifi.where())
        with urllib.request.urlopen(url, context=context) as response:
            data = json.loads(response.read())

        precip  = data["daily"]["precipitation_sum"]
        mm_48hr = round(precip[1] + precip[2], 1)
        return mm_48hr

    except Exception as e:
        print(f"Warning: Could not fetch rainfall for {lat},{lng} — {e}")
        return 0.0


# =============================================
# VILLAGE VULNERABILITY SCORER
# =============================================

def score_village(village):

    score = 0

    # Factor 1: Population (25%)
    population = village["population"]
    if   population > 10000: score += 25
    elif population > 5000:  score += 20
    elif population > 1000:  score += 15
    elif population > 500:   score += 10
    else:                    score += 5

    # Factor 2: GLOF Travel Time (20%)
    travel_time = village["travel_time"]
    if   travel_time < 20:  score += 20
    elif travel_time < 40:  score += 15
    elif travel_time < 60:  score += 10
    elif travel_time < 90:  score += 5
    else:                   score += 0

    # Factor 3: Rainfall Risk (20%)
    rainfall_risk = village["rainfall_risk"]
    if   rainfall_risk == "HIGH":   score += 20
    elif rainfall_risk == "MEDIUM": score += 12
    else:                           score += 4

    # Factor 4: Road Safety (20%)
    if not village["road_safe"]:
        score += 20

    # Factor 5: Historical Event (15%)
    if village["historical_event"]:
        score += 15

    return score


# =============================================
# RISK LEVEL FROM SCORE
# =============================================

def get_risk_level(score):
    if score >= 70: return "HIGH"
    if score >= 45: return "MEDIUM"
    return "LOW"


# =============================================
# DISTRICT COORDINATES
# =============================================

DISTRICTS = [
    {"name": "Uttarkashi",    "lat": 30.7268, "lng": 78.4354},
    {"name": "Chamoli",       "lat": 30.4021, "lng": 79.3215},
    {"name": "Rudraprayag",   "lat": 30.2847, "lng": 78.9816},
    {"name": "Tehri Garhwal", "lat": 30.3780, "lng": 78.4322},
    {"name": "Pithoragarh",   "lat": 29.5829, "lng": 80.2181},
    {"name": "Haridwar",      "lat": 29.9457, "lng": 78.1642}
]


# =============================================
# VILLAGE DATA
# =============================================

villages = [
    {
        "name":             "Kedarnath",
        "district":         "Rudraprayag",
        "population":       1200,
        "travel_time":      23,
        "rainfall_risk":    "LOW",
        "road_safe":        False,
        "historical_event": True,
        "threat_type":      "BOTH"
    },
    {
        "name":             "Gangotri",
        "district":         "Uttarkashi",
        "population":       3400,
        "travel_time":      18,
        "rainfall_risk":    "LOW",
        "road_safe":        False,
        "historical_event": True,
        "threat_type":      "BOTH"
    },
    {
        "name":             "Joshimath",
        "district":         "Chamoli",
        "population":       16500,
        "travel_time":      41,
        "rainfall_risk":    "LOW",
        "road_safe":        False,
        "historical_event": True,
        "threat_type":      "BOTH"
    },
    {
        "name":             "Raini",
        "district":         "Chamoli",
        "population":       450,
        "travel_time":      15,
        "rainfall_risk":    "LOW",
        "road_safe":        False,
        "historical_event": True,
        "threat_type":      "BOTH"
    },
    {
        "name":             "Tapovan",
        "district":         "Chamoli",
        "population":       350,
        "travel_time":      12,
        "rainfall_risk":    "LOW",
        "road_safe":        False,
        "historical_event": True,
        "threat_type":      "BOTH"
    },
    {
        "name":             "Dharali",
        "district":         "Uttarkashi",
        "population":       2100,
        "travel_time":      31,
        "rainfall_risk":    "LOW",
        "road_safe":        False,
        "historical_event": True,
        "threat_type":      "BOTH"
    },
    {
        "name":             "Munsiyari",
        "district":         "Pithoragarh",
        "population":       5200,
        "travel_time":      55,
        "rainfall_risk":    "LOW",
        "road_safe":        True,
        "historical_event": False,
        "threat_type":      "GLOF"
    },
    {
        "name":             "Haridwar",
        "district":         "Haridwar",
        "population":       228832,
        "travel_time":      999,
        "rainfall_risk":    "LOW",
        "road_safe":        True,
        "historical_event": False,
        "threat_type":      "FLOOD"
    }
]


# =============================================
# MAIN
# =============================================

if __name__ == "__main__":

    print("=" * 55)
    print("UMBRELLA — Live Village Risk Assessment")
    print("=" * 55)

    # Step 1 — Fetch live rainfall for all districts
    print("\n📡 Fetching live rainfall data...\n")

    rainfall_by_district = {}

    for district in DISTRICTS:
        mm   = fetch_rainfall(district["lat"], district["lng"])
        risk = get_rainfall_risk(mm)
        rainfall_by_district[district["name"]] = {
            "mm":   mm,
            "risk": risk
        }
        print(f"  {district['name']:<16} {mm}mm  →  {risk}")

    # Step 2 — Assign live rainfall risk to each village
    for village in villages:
        district_name = village["district"]
        if district_name in rainfall_by_district:
            village["rainfall_risk"] = \
                rainfall_by_district[district_name]["risk"]

    # Step 3 — Score all villages with live data
    print("\n" + "=" * 55)
    print("VILLAGE RISK SCORES — driven by live rainfall")
    print("=" * 55 + "\n")

    results = []
    for village in villages:
        score      = score_village(village)
        risk_level = get_risk_level(score)
        results.append({
            "name":       village["name"],
            "district":   village["district"],
            "score":      score,
            "risk_level": risk_level,
            "threat":     village["threat_type"],
            "rainfall":   village["rainfall_risk"]
        })

    # Sort highest score first
    results.sort(key=lambda x: x["score"], reverse=True)

    # Print results table
    for r in results:
        print(
            f"{r['risk_level']:<8} "
            f"Score: {r['score']:<4} "
            f"{r['name']:<20} "
            f"District: {r['district']:<16} "
            f"Rainfall: {r['rainfall']}"
        )

    print("\n" + "=" * 55)
    print(f"Villages assessed: {len(results)}")

    high = [r for r in results if r["risk_level"] == "HIGH"]
    med  = [r for r in results if r["risk_level"] == "MEDIUM"]
    low  = [r for r in results if r["risk_level"] == "LOW"]

    print(f"🔴 High risk:   {len(high)} villages")
    print(f"🟠 Medium risk: {len(med)} villages")
    print(f"🟢 Low risk:    {len(low)} villages")
    print("=" * 55)
