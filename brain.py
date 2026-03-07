# Umbrella — Backend Brain
# Formula: NDMA Risk = Hazard + Vulnerability + Exposure

import urllib.request
import json
import ssl
import certifi
from datetime import datetime


# ── RAINFALL RISK ──────────────────────────────────────────

def get_rainfall_risk(mm_48hr):
    if mm_48hr >= 115: return "HIGH"
    if mm_48hr >= 65:  return "MEDIUM"
    return "LOW"


# ── PILGRIMAGE SEASON ──────────────────────────────────────
# Char Dham yatra: May–November (months 5–11)
# Population multiplier: 30x for pilgrimage villages in season

PILGRIMAGE_MULTIPLIER = 30

def is_pilgrimage_season():
    month = datetime.now().month
    return 5 <= month <= 11

def effective_population(population, pilgrimage):
    if pilgrimage and is_pilgrimage_season():
        return population * PILGRIMAGE_MULTIPLIER
    return population


# ── FETCH LIVE RAINFALL ────────────────────────────────────

def fetch_rainfall(lat, lng):
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lng}"
        f"&daily=precipitation_sum"
        f"&past_days=2&forecast_days=1"
        f"&timezone=Asia%2FKolkata"
    )
    try:
        context = ssl.create_default_context(cafile=certifi.where())
        with urllib.request.urlopen(url, context=context) as response:
            data = json.loads(response.read())
        precip = data["daily"]["precipitation_sum"]
        return round(precip[1] + precip[2], 1)
    except Exception as e:
        print(f"Warning: Could not fetch rainfall for {lat},{lng} — {e}")
        return 0.0


# ── VILLAGE SCORER — NDMA FRAMEWORK ───────────────────────
#
#  HAZARD        (50pts) — dynamic, changes with weather
#    Rainfall      30pts — primary signal
#    GLOF Travel   20pts — proximity to glacial lake
#
#  VULNERABILITY  (30pts) — permanent geographic facts
#    Road Access   15pts — number of routes into village
#    Historical    15pts — past disaster record
#
#  EXPOSURE       (20pts) — population at risk
#    Population    20pts — effective population (pilgrimage-adjusted)
#
#  Max score: 100

def score_village(village):
    score = 0

    # HAZARD
    rainfall_risk = village["rainfall_risk"]
    if   rainfall_risk == "HIGH":   score += 30
    elif rainfall_risk == "MEDIUM": score += 18
    else:                           score += 6

    travel_time = village["travel_time"]
    if   travel_time < 20:  score += 20
    elif travel_time < 40:  score += 15
    elif travel_time < 60:  score += 10
    elif travel_time < 90:  score += 5
    else:                   score += 0

    # VULNERABILITY
    road_access = village.get("road_access", 1)
    if   road_access == 1: score += 15
    elif road_access == 2: score += 8
    else:                  score += 0

    if village["historical_event"]:
        score += 15

    # EXPOSURE — use effective population (pilgrimage-adjusted)
    pop = effective_population(village["population"], village.get("pilgrimage", False))
    if   pop > 10000: score += 20
    elif pop > 5000:  score += 16
    elif pop > 1000:  score += 12
    elif pop > 500:   score += 8
    else:             score += 4

    return score


# ── RISK LEVEL ─────────────────────────────────────────────

def get_risk_level(score):
    if score >= 70: return "HIGH"
    if score >= 45: return "MEDIUM"
    return "LOW"


# ── DISTRICT COORDINATES ───────────────────────────────────

DISTRICTS = [
    {"name": "Uttarkashi",    "lat": 30.7268, "lng": 78.4354},
    {"name": "Chamoli",       "lat": 30.4021, "lng": 79.3215},
    {"name": "Rudraprayag",   "lat": 30.2847, "lng": 78.9816},
    {"name": "Tehri Garhwal", "lat": 30.3780, "lng": 78.4322},
    {"name": "Pithoragarh",   "lat": 29.5829, "lng": 80.2181},
    {"name": "Haridwar",      "lat": 29.9457, "lng": 78.1642}
]


# ── READ VILLAGES FROM DATABASE ────────────────────────────

def get_villages_from_db():
    import sqlite3, os
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "umbrella.db")
    conn   = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name, district, population, travel_time,
               road_access, historical_event, threat_type, pilgrimage
        FROM villages ORDER BY id
    """)
    rows = cursor.fetchall()
    conn.close()

    villages = []
    for row in rows:
        villages.append({
            "name":             row[0],
            "district":         row[1],
            "population":       row[2],
            "travel_time":      row[3],
            "road_access":      row[4],
            "historical_event": bool(row[5]),
            "threat_type":      row[6],
            "pilgrimage":       bool(row[7]) if row[7] is not None else False,
            "rainfall_risk":    "LOW"
        })
    return villages


# ── MAIN ───────────────────────────────────────────────────

if __name__ == "__main__":
    season = "PILGRIMAGE SEASON (May–Nov)" if is_pilgrimage_season() else "OFF SEASON"
    print("=" * 60)
    print("UMBRELLA — NDMA Risk Assessment")
    print(f"Hazard + Vulnerability + Exposure  [{season}]")
    print("=" * 60)

    villages = get_villages_from_db()
    print(f"\n✓ Loaded {len(villages)} villages\n")
    print("📡 Fetching live rainfall...\n")

    rainfall_by_district = {}
    for d in DISTRICTS:
        mm   = fetch_rainfall(d["lat"], d["lng"])
        risk = get_rainfall_risk(mm)
        rainfall_by_district[d["name"]] = {"mm": mm, "risk": risk}
        print(f"  {d['name']:<16} {mm}mm → {risk}")

    for v in villages:
        if v["district"] in rainfall_by_district:
            v["rainfall_risk"] = rainfall_by_district[v["district"]]["risk"]

    results = []
    for v in villages:
        score = score_village(v)
        eff_pop = effective_population(v["population"], v.get("pilgrimage", False))
        results.append({
            "name": v["name"], "district": v["district"],
            "score": score, "risk_level": get_risk_level(score),
            "rainfall": v["rainfall_risk"], "road_access": v["road_access"],
            "pilgrimage": v.get("pilgrimage", False), "eff_pop": eff_pop
        })

    results.sort(key=lambda x: x["score"], reverse=True)

    print(f"\n{'RISK':<8} {'SCORE':<7} {'VILLAGE':<22} {'DISTRICT':<18} {'POP':<10} RAINFALL")
    print("-" * 75)
    for r in results:
        pop_str = f"{r['eff_pop']:,}" + (" 🛕" if r["pilgrimage"] and is_pilgrimage_season() else "")
        print(f"{r['risk_level']:<8} {r['score']:<7} {r['name']:<22} {r['district']:<18} {pop_str:<10} {r['rainfall']}")

    high = [r for r in results if r["risk_level"] == "HIGH"]
    med  = [r for r in results if r["risk_level"] == "MEDIUM"]
    low  = [r for r in results if r["risk_level"] == "LOW"]
    print(f"\n🔴 High: {len(high)}  🟠 Medium: {len(med)}  🟢 Low: {len(low)}")
    if is_pilgrimage_season():
        print(f"🛕 Pilgrimage season active — population x{PILGRIMAGE_MULTIPLIER} for Char Dham villages")
    print("=" * 60)