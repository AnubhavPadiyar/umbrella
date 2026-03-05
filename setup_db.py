# setup_db.py
# Run this to RESET the database with the new schema
# road_safe (boolean) replaced by road_access (integer: 1, 2, or 3+)

import sqlite3

conn   = sqlite3.connect("umbrella.db")
cursor = conn.cursor()

# Drop old table and recreate with new schema
cursor.execute("DROP TABLE IF EXISTS villages")

cursor.execute("""
    CREATE TABLE villages (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        name             TEXT    NOT NULL,
        district         TEXT    NOT NULL,
        population       INTEGER NOT NULL,
        travel_time      INTEGER NOT NULL,
        road_access      INTEGER NOT NULL DEFAULT 1,
        historical_event INTEGER NOT NULL,
        threat_type      TEXT    NOT NULL
    )
""")

print("✓ Villages table created with new schema (road_access)")

# road_access values:
#   1 = single route — fully isolated when blocked (highest vulnerability)
#   2 = two routes   — partial access
#   3 = three+ routes — multiple alternatives (lowest vulnerability)

villages = [
    # name               district         pop     travel  road_access  history  threat
    ("Kedarnath",        "Rudraprayag",   1200,   23,     1,           1,       "BOTH"),
    ("Gangotri",         "Uttarkashi",    3400,   18,     1,           1,       "BOTH"),
    ("Dharali",          "Uttarkashi",    2100,   31,     1,           1,       "BOTH"),
    ("Joshimath",        "Chamoli",       16500,  41,     1,           1,       "BOTH"),
    ("Raini",            "Chamoli",       450,    15,     1,           1,       "BOTH"),
    ("Tapovan",          "Chamoli",       350,    12,     1,           1,       "BOTH"),
    ("Govindghat",       "Chamoli",       800,    50,     1,           1,       "BOTH"),
    ("Badrinath",        "Chamoli",       2800,   67,     1,           0,       "GLOF"),
    ("Mana Village",     "Chamoli",       600,    72,     1,           0,       "GLOF"),
    ("Munsiyari",        "Pithoragarh",   5200,   55,     2,           0,       "GLOF"),
    ("Pithoragarh Town", "Pithoragarh",   12000,  120,    3,           0,       "GLOF"),
    ("Uttarkashi Town",  "Uttarkashi",    8900,   45,     2,           1,       "FLOOD"),
    ("Bhatwari",         "Uttarkashi",    3100,   60,     2,           0,       "FLOOD"),
    ("Ghansali",         "Tehri Garhwal", 4200,   90,     2,           0,       "FLOOD"),
    ("Haridwar",         "Haridwar",      228832, 999,    3,           0,       "FLOOD"),
]

cursor.executemany("""
    INSERT INTO villages
        (name, district, population, travel_time,
         road_access, historical_event, threat_type)
    VALUES (?, ?, ?, ?, ?, ?, ?)
""", villages)

print(f"✓ {len(villages)} villages inserted with road_access values")

cursor.execute("SELECT id, name, district, road_access FROM villages")
rows = cursor.fetchall()
print("\n--- Villages in database ---")
for row in rows:
    routes = "1 route" if row[3]==1 else f"{row[3]} routes"
    print(f"  [{row[0]}] {row[1]:<22} {row[2]:<16} {routes}")

conn.commit()
conn.close()
print("\n✓ Database ready")