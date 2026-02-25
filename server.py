# Umbrella — Flask Server
# This turns brain.py into a web API

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

# Create the Flask app
app = Flask(__name__)
CORS(app)


# =============================================
# ROUTE 1 — Health Check
# Visit: http://localhost:5000/
# =============================================

@app.route("/")
def home():
    return jsonify({
        "status":  "online",
        "system":  "Umbrella",
        "version": "1.0"
    })


# =============================================
# ROUTE 2 — Live Rainfall
# Visit: http://localhost:5000/rainfall
# =============================================

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

    return jsonify({
        "status":    "success",
        "districts": results
    })


# =============================================
# ROUTE 3 — Village Scores
# Visit: http://localhost:5000/villages
# =============================================

@app.route("/villages")
def village_scores():

    # Step 1 — fetch live rainfall
    rainfall_by_district = {}

    for district in DISTRICTS:
        mm   = fetch_rainfall(district["lat"], district["lng"])
        risk = get_rainfall_risk(mm)
        rainfall_by_district[district["name"]] = risk

    # Step 2 — assign live rainfall to each village
    villages = get_villages_from_db()

    for village in villages:
        district_name = village["district"]
        if district_name in rainfall_by_district:
            village["rainfall_risk"] = rainfall_by_district[district_name]

    # Step 3 — score every village
    results = []

    for village in villages:
        score      = score_village(village)
        risk_level = get_risk_level(score)

        results.append({
            "name":          village["name"],
            "district":      village["district"],
            "score":         score,
            "risk_level":    risk_level,
            "threat_type":   village["threat_type"],
            "rainfall_risk": village["rainfall_risk"],
            "population":    village["population"],
            "travel_time":   village["travel_time"],
            "road_safe":     village["road_safe"]
        })

    # Sort highest score first
    results.sort(key=lambda x: x["score"], reverse=True)

    return jsonify({
        "status":   "success",
        "count":    len(results),
        "villages": results
    })
    
    # =============================================
# ROUTE 4 — Add a new village
# Called when admin submits the form
# =============================================

@app.route("/admin/add-village", methods=["POST"])
def add_village():
    import sqlite3, os
    data = request.get_json()

    name             = data.get("name")
    district         = data.get("district")
    population       = int(data.get("population"))
    travel_time      = int(data.get("travel_time"))
    road_safe        = int(data.get("road_safe"))
    historical_event = int(data.get("historical_event"))
    threat_type      = data.get("threat_type")

    db_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "umbrella.db"
    )
    conn   = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO villages
            (name, district, population, travel_time,
             road_safe, historical_event, threat_type)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (name, district, population, travel_time,
          road_safe, historical_event, threat_type))

    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return jsonify({
        "status":  "success",
        "message": f"Village '{name}' added",
        "id":      new_id
    })


# =============================================
# ROUTE 5 — Delete a village
# =============================================

@app.route("/admin/delete-village/<int:village_id>", methods=["DELETE"])
def delete_village(village_id):
    import sqlite3, os

    db_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "umbrella.db"
    )
    conn   = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM villages WHERE id = ?", (village_id,))
    conn.commit()
    conn.close()

    return jsonify({
        "status":  "success",
        "message": f"Village {village_id} deleted"
    })


# =============================================
# ROUTE 6 — Get all villages (raw, no scoring)
# For the admin panel table
# =============================================

@app.route("/admin/villages")
def admin_villages():
    import sqlite3, os

    db_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "umbrella.db"
    )
    conn   = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, district, population,
               travel_time, road_safe, historical_event, threat_type
        FROM villages
        ORDER BY id
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
            "road_safe":        bool(row[5]),
            "historical_event": bool(row[6]),
            "threat_type":      row[7]
        })

    return jsonify({
        "status":   "success",
        "count":    len(villages),
        "villages": villages
    })


# =============================================
# START THE SERVER
# =============================================

if __name__ == "__main__":
    print("=" * 45)
    print("☂  Umbrella Server Starting...")
    print("=" * 45)
    print("  Home:     http://localhost:5000/")
    print("  Rainfall: http://localhost:5000/rainfall")
    print("  Villages: http://localhost:5000/villages")
    print("=" * 45)

    import os
port = int(os.environ.get("PORT", 5001))
app.run(host="0.0.0.0", debug=False, port=port)
