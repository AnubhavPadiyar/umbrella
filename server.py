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
        results.append({
            "name":             village["name"],
            "district":         village["district"],
            "score":            score,
            "risk_level":       risk_level,
            "threat_type":      village["threat_type"],
            "rainfall_risk":    village["rainfall_risk"],
            "population":       village["population"],
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


# ── START ──────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("☂  Umbrella Server v2.0")
    print("=" * 50)
    import os
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", debug=False, port=port)
