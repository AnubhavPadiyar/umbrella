# Umbrella — Flask Server v2.0
# NDMA Formula — road_access replaces road_safe
# Auto-migrates database on startup

from flask import Flask, jsonify, request
from flask_cors import CORS
from brain import (
    fetch_rainfall,
    get_rainfall_risk,
    score_village,
    get_risk_level,
    get_villages_from_db,
    effective_population,
    is_pilgrimage_season,
    DISTRICTS
)

app = Flask(__name__)
CORS(app)


# ── AUTO-MIGRATE DATABASE ON STARTUP ──────────────────────
# Runs every time server starts — safe to run repeatedly
# Adds road_access column if it doesn't exist yet

def auto_migrate():
    import sqlite3, os
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "umbrella.db")
    conn   = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(villages)")
    columns = [row[1] for row in cursor.fetchall()]

    if "road_access" not in columns:
        print("Running migration: adding road_access column...")
        cursor.execute("ALTER TABLE villages ADD COLUMN road_access INTEGER NOT NULL DEFAULT 1")

        # Set from road_safe if it exists
        if "road_safe" in columns:
            cursor.execute("UPDATE villages SET road_access = 1 WHERE road_safe = 0")
            cursor.execute("UPDATE villages SET road_access = 2 WHERE road_safe = 1")

        # Apply correct geographic values
        road_map = {
            "Kedarnath": 1, "Gangotri": 1, "Dharali": 1,
            "Joshimath": 1, "Raini": 1, "Tapovan": 1,
            "Govindghat": 1, "Badrinath": 1, "Mana Village": 1,
            "Munsiyari": 2, "Pithoragarh Town": 3,
            "Uttarkashi Town": 2, "Bhatwari": 2,
            "Ghansali": 2, "Haridwar": 3,
        }
        for name, routes in road_map.items():
            cursor.execute("UPDATE villages SET road_access = ? WHERE name = ?", (routes, name))

        conn.commit()
        print("✓ Migration complete — road_access column added")
    else:
        print("✓ Database schema OK — road_access exists")

    # Add pilgrimage column if missing
    if "pilgrimage" not in columns:
        print("Running migration: adding pilgrimage column...")
        cursor.execute("ALTER TABLE villages ADD COLUMN pilgrimage INTEGER NOT NULL DEFAULT 0")
        # Mark Char Dham pilgrimage villages
        pilgrimage_villages = ["Kedarnath", "Badrinath", "Gangotri", "Govindghat", "Tapovan", "Mana Village"]
        for name in pilgrimage_villages:
            cursor.execute("UPDATE villages SET pilgrimage = 1 WHERE name = ?", (name,))
        conn.commit()
        print("✓ Migration complete — pilgrimage column added")
    else:
        print("✓ Database schema OK — pilgrimage exists")

    # Create incidents table if missing
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            time      TEXT NOT NULL,
            source    TEXT NOT NULL,
            text      TEXT NOT NULL,
            officer   TEXT,
            risk      TEXT
        )
    """)
    conn.commit()
    print("✓ Database schema OK — incidents table exists")

    conn.close()

auto_migrate()


# ── ROUTE 1 — Health Check ─────────────────────────────────

@app.route("/")
def home():
    return jsonify({"status": "online", "system": "Umbrella", "version": "2.0"})


# ── ROUTE 2 — Live Rainfall ────────────────────────────────

@app.route("/rainfall")
def rainfall():
    results = []
    for district in DISTRICTS:
        mm   = fetch_rainfall(district["lat"], district["lng"])
        risk = get_rainfall_risk(mm)
        results.append({
            "district": district["name"],
            "mm_48hr":  mm,
            "risk":     risk
        })
    return jsonify({"status": "success", "districts": results})


# ── ROUTE 3 — Village Scores (live) ───────────────────────

@app.route("/villages")
def village_scores():
    rainfall_by_district = {}
    for district in DISTRICTS:
        mm   = fetch_rainfall(district["lat"], district["lng"])
        risk = get_rainfall_risk(mm)
        rainfall_by_district[district["name"]] = risk

    villages = get_villages_from_db()
    for village in villages:
        if village["district"] in rainfall_by_district:
            village["rainfall_risk"] = rainfall_by_district[village["district"]]

    results = []
    for village in villages:
        score      = score_village(village)
        risk_level = get_risk_level(score)
        eff_pop    = effective_population(village["population"], village.get("pilgrimage", False))
        results.append({
            "name":             village["name"],
            "district":         village["district"],
            "score":            score,
            "risk_level":       risk_level,
            "threat_type":      village["threat_type"],
            "rainfall_risk":    village["rainfall_risk"],
            "population":       village["population"],
            "effective_population": eff_pop,
            "pilgrimage":       village.get("pilgrimage", False),
            "pilgrimage_season": is_pilgrimage_season(),
            "travel_time":      village["travel_time"],
            "road_access":      village["road_access"],
            "historical_event": village["historical_event"]
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return jsonify({"status": "success", "count": len(results), "villages": results})


# ── ROUTE 4 — Admin: Get All Villages ─────────────────────

@app.route("/admin/villages")
def admin_villages():
    import sqlite3, os
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "umbrella.db")
    conn   = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, district, population,
               travel_time, road_access, historical_event, threat_type
        FROM villages ORDER BY id
    """)
    rows = cursor.fetchall()
    conn.close()

    villages = []
    for row in rows:
        villages.append({
            "id":               row[0],
            "name":             row[1],
            "district":         row[2],
            "population":       row[3],
            "travel_time":      row[4],
            "road_access":      row[5],
            "historical_event": bool(row[6]),
            "threat_type":      row[7]
        })
    return jsonify({"status": "success", "count": len(villages), "villages": villages})


# ── ROUTE 5 — Admin: Add Village ──────────────────────────

@app.route("/admin/add-village", methods=["POST"])
def add_village():
    import sqlite3, os
    data = request.get_json()

    name             = data.get("name")
    district         = data.get("district")
    population       = int(data.get("population"))
    travel_time      = int(data.get("travel_time"))
    road_access      = int(data.get("road_access", 1))
    historical_event = int(data.get("historical_event", 0))
    threat_type      = data.get("threat_type")

    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "umbrella.db")
    conn   = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO villages
            (name, district, population, travel_time,
             road_access, historical_event, threat_type)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (name, district, population, travel_time,
          road_access, historical_event, threat_type))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return jsonify({"status": "success", "message": f"Village '{name}' added", "id": new_id})


# ── ROUTE 6 — Admin: Edit Village ─────────────────────────

@app.route("/admin/edit-village/<int:village_id>", methods=["PUT"])
def edit_village(village_id):
    import sqlite3, os
    data = request.get_json()

    name             = data.get("name")
    district         = data.get("district")
    population       = int(data.get("population"))
    travel_time      = int(data.get("travel_time"))
    road_access      = int(data.get("road_access", 1))
    historical_event = int(data.get("historical_event", 0))
    threat_type      = data.get("threat_type")

    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "umbrella.db")
    conn   = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE villages SET
            name=?, district=?, population=?, travel_time=?,
            road_access=?, historical_event=?, threat_type=?
        WHERE id=?
    """, (name, district, population, travel_time,
          road_access, historical_event, threat_type, village_id))
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "message": f"Village {village_id} updated"})


# ── ROUTE 7 — Admin: Delete Village ───────────────────────

@app.route("/admin/delete-village/<int:village_id>", methods=["DELETE"])
def delete_village(village_id):
    import sqlite3, os
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "umbrella.db")
    conn   = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM villages WHERE id = ?", (village_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": f"Village {village_id} deleted"})


# ── ROUTE 8 — Live Earthquake Data ────────────────────────

@app.route("/earthquake")
def earthquake():
    import urllib.request, json, ssl, certifi

    # USGS API — earthquakes M2.5+ within 350km of Uttarakhand centre
    url = (
        "https://earthquake.usgs.gov/fdsnws/event/1/query"
        "?format=geojson"
        "&latitude=30.5&longitude=79.0"
        "&maxradiuskm=350"
        "&minmagnitude=2.5"
        "&orderby=time"
        "&limit=20"
    )

    # Seismic zone data for our villages (static — NDMA classification)
    village_zones = {
        "Kedarnath":        {"zone": "V", "district": "Rudraprayag", "lat": 30.7346, "lng": 79.0669},
        "Gangotri":         {"zone": "V", "district": "Uttarkashi",  "lat": 30.9940, "lng": 79.0770},
        "Dharali":          {"zone": "V", "district": "Uttarkashi",  "lat": 30.9500, "lng": 78.9800},
        "Joshimath":        {"zone": "V", "district": "Chamoli",     "lat": 30.5580, "lng": 79.5640},
        "Raini":            {"zone": "V", "district": "Chamoli",     "lat": 30.5200, "lng": 79.7200},
        "Tapovan":          {"zone": "V", "district": "Chamoli",     "lat": 30.4900, "lng": 79.6700},
        "Govindghat":       {"zone": "V", "district": "Chamoli",     "lat": 30.5400, "lng": 79.6600},
        "Badrinath":        {"zone": "V", "district": "Chamoli",     "lat": 30.7433, "lng": 79.4938},
        "Mana Village":     {"zone": "V", "district": "Chamoli",     "lat": 30.7700, "lng": 79.5500},
        "Munsiyari":        {"zone": "IV","district": "Pithoragarh", "lat": 30.0678, "lng": 80.2378},
        "Pithoragarh Town": {"zone": "IV","district": "Pithoragarh", "lat": 29.5829, "lng": 80.2181},
        "Uttarkashi Town":  {"zone": "V", "district": "Uttarkashi",  "lat": 30.7268, "lng": 78.4354},
        "Bhatwari":         {"zone": "V", "district": "Uttarkashi",  "lat": 30.8500, "lng": 78.6000},
        "Ghansali":         {"zone": "IV","district": "Tehri Garhwal","lat": 30.4200, "lng": 78.6500},
        "Haridwar":         {"zone": "III","district": "Haridwar",   "lat": 29.9457, "lng": 78.1642},
    }

    try:
        context = ssl.create_default_context(cafile=certifi.where())
        with urllib.request.urlopen(url, context=context, timeout=10) as response:
            data = json.loads(response.read())

        quakes = []
        for feature in data["features"]:
            props = feature["properties"]
            coords = feature["geometry"]["coordinates"]
            quakes.append({
                "magnitude": props["mag"],
                "place":     props["place"],
                "time":      props["time"],
                "depth_km":  round(coords[2], 1),
                "lng":       coords[0],
                "lat":       coords[1],
                "url":       props["url"]
            })

        # Find nearest village for each quake
        import math
        def haversine(lat1, lng1, lat2, lng2):
            R = 6371
            dlat = math.radians(lat2 - lat1)
            dlng = math.radians(lng2 - lng1)
            a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
            return round(R * 2 * math.asin(math.sqrt(a)), 1)

        for q in quakes:
            nearest, min_dist = None, 9999
            for name, v in village_zones.items():
                d = haversine(q["lat"], q["lng"], v["lat"], v["lng"])
                if d < min_dist:
                    min_dist = d
                    nearest = name
            q["nearest_village"] = nearest
            q["nearest_km"] = min_dist

        # Build village seismic risk list
        villages_seismic = []
        for name, v in village_zones.items():
            # Find closest recent quake
            nearest_quake = None
            min_dist = 9999
            for q in quakes:
                d = haversine(v["lat"], v["lng"], q["lat"], q["lng"])
                if d < min_dist:
                    min_dist = d
                    nearest_quake = q

            zone_risk = {"V": "HIGH", "IV": "MEDIUM", "III": "LOW"}[v["zone"]]
            villages_seismic.append({
                "name":            name,
                "district":        v["district"],
                "zone":            v["zone"],
                "lat":             v["lat"],
                "lng":             v["lng"],
                "risk_level":      zone_risk,
                "nearest_quake_km": min_dist if nearest_quake else None,
                "nearest_quake_mag": nearest_quake["magnitude"] if nearest_quake else None,
            })

        return jsonify({
            "status":   "success",
            "quakes":   quakes,
            "villages": villages_seismic,
            "total":    len(quakes)
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e), "quakes": [], "villages": []})


# ── ROUTE 9 — Forest Fire Data (NASA FIRMS) ───────────────

@app.route("/fire")
def fire():
    import urllib.request, json, ssl, certifi, csv, io, math

    FIRMS_KEY = "2823ed85154f2f822d76dcdac6bdac6d"

    # VIIRS SNPP — last 24hrs, India bounding box covering Uttarakhand
    # bbox: west,south,east,north
    url = (
        f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{FIRMS_KEY}"
        f"/VIIRS_SNPP_NRT/77.0,28.5,81.5,31.5/1"
    )

    village_coords = {
        "Kedarnath":        (30.7346, 79.0669, "Rudraprayag"),
        "Gangotri":         (30.9940, 79.0770, "Uttarkashi"),
        "Dharali":          (30.9500, 78.9800, "Uttarkashi"),
        "Joshimath":        (30.5580, 79.5640, "Chamoli"),
        "Raini":            (30.5200, 79.7200, "Chamoli"),
        "Tapovan":          (30.4900, 79.6700, "Chamoli"),
        "Govindghat":       (30.5400, 79.6600, "Chamoli"),
        "Badrinath":        (30.7433, 79.4938, "Chamoli"),
        "Mana Village":     (30.7700, 79.5500, "Chamoli"),
        "Munsiyari":        (30.0678, 80.2378, "Pithoragarh"),
        "Pithoragarh Town": (29.5829, 80.2181, "Pithoragarh"),
        "Uttarkashi Town":  (30.7268, 78.4354, "Uttarkashi"),
        "Bhatwari":         (30.8500, 78.6000, "Uttarkashi"),
        "Ghansali":         (30.4200, 78.6500, "Tehri Garhwal"),
        "Haridwar":         (29.9457, 78.1642, "Haridwar"),
    }

    # Forest cover % by district (FSI 2021 report)
    forest_cover = {
        "Uttarkashi": 72, "Chamoli": 68, "Rudraprayag": 65,
        "Tehri Garhwal": 55, "Pithoragarh": 58, "Haridwar": 18
    }

    def haversine(lat1, lng1, lat2, lng2):
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
        return round(R * 2 * math.asin(math.sqrt(a)), 1)

    try:
        context = ssl.create_default_context(cafile=certifi.where())
        with urllib.request.urlopen(url, context=context, timeout=15) as response:
            raw = response.read().decode("utf-8")

        fires = []
        reader = csv.DictReader(io.StringIO(raw))
        for row in reader:
            try:
                fires.append({
                    "lat":        float(row["latitude"]),
                    "lng":        float(row["longitude"]),
                    "brightness": float(row.get("bright_ti4", row.get("brightness", 0))),
                    "frp":        float(row.get("frp", 0)),
                    "acq_date":   row.get("acq_date", ""),
                    "acq_time":   row.get("acq_time", ""),
                    "confidence": row.get("confidence", "n"),
                    "satellite":  row.get("satellite", "VIIRS"),
                })
            except:
                continue

        # Find nearest fire for each village
        villages_fire = []
        for name, (vlat, vlng, district) in village_coords.items():
            nearest_dist = 9999
            nearest_fire = None
            for f in fires:
                d = haversine(vlat, vlng, f["lat"], f["lng"])
                if d < nearest_dist:
                    nearest_dist = d
                    nearest_fire = f

            fc = forest_cover.get(district, 40)

            # Risk: proximity + forest cover
            if nearest_dist < 20:   risk = "HIGH"
            elif nearest_dist < 50: risk = "MEDIUM" if fc > 50 else "LOW"
            elif nearest_dist < 100:risk = "LOW"     if fc < 50 else "MEDIUM"
            else:                   risk = "LOW"

            # Boost if very high forest cover
            if fc >= 65 and nearest_dist < 80 and risk == "LOW":
                risk = "MEDIUM"

            villages_fire.append({
                "name":           name,
                "district":       district,
                "forest_cover":   fc,
                "nearest_fire_km": nearest_dist if nearest_fire else None,
                "nearest_fire_date": nearest_fire["acq_date"] if nearest_fire else None,
                "risk_level":     risk,
                "lat": vlat, "lng": vlng
            })

        villages_fire.sort(key=lambda x: (0 if x["risk_level"]=="HIGH" else 1 if x["risk_level"]=="MEDIUM" else 2))

        return jsonify({
            "status":   "success",
            "fires":    fires,
            "villages": villages_fire,
            "total":    len(fires)
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e), "fires": [], "villages": []})


# ── ROUTE 10 — Get Incidents ──────────────────────────────

@app.route("/incidents")
def get_incidents():
    import sqlite3, os
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "umbrella.db")
    conn   = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, time, source, text, officer, risk FROM incidents ORDER BY id DESC LIMIT 200")
    rows = cursor.fetchall()
    conn.close()
    incidents = [{"id":r[0],"time":r[1],"source":r[2],"text":r[3],"officer":r[4],"risk":r[5]} for r in rows]
    return jsonify({"status":"success","count":len(incidents),"incidents":incidents})


# ── ROUTE 11 — Add Incident ────────────────────────────────

@app.route("/incidents", methods=["POST"])
def add_incident():
    import sqlite3, os
    data    = request.get_json()
    time    = data.get("time")
    source  = data.get("source","manual")
    text    = data.get("text","")
    officer = data.get("officer")
    risk    = data.get("risk")
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "umbrella.db")
    conn   = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO incidents (time,source,text,officer,risk) VALUES (?,?,?,?,?)",
                   (time, source, text, officer, risk))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return jsonify({"status":"success","id":new_id})


# ── ROUTE 12 — Delete Incident ─────────────────────────────

@app.route("/incidents/<int:incident_id>", methods=["DELETE"])
def delete_incident(incident_id):
    import sqlite3, os
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "umbrella.db")
    conn   = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM incidents WHERE id=?", (incident_id,))
    conn.commit()
    conn.close()
    return jsonify({"status":"success","message":f"Incident {incident_id} deleted"})


# ── START ──────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("☂  Umbrella Server v2.0")
    print("=" * 50)
    import os
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", debug=False, port=port)
