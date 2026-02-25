# setup_db.py
# Run this ONCE to create your database
# After that, your data lives in umbrella.db

import sqlite3

# Connect to database
# This creates the file umbrella.db if it doesn't exist
conn = sqlite3.connect("umbrella.db")

# A cursor is what you use to send commands to the database
cursor = conn.cursor()

# =============================================
# CREATE THE VILLAGES TABLE
# =============================================

cursor.execute("""
    CREATE TABLE IF NOT EXISTS villages (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        name             TEXT    NOT NULL,
        district         TEXT    NOT NULL,
        population       INTEGER NOT NULL,
        travel_time      INTEGER NOT NULL,
        road_safe        INTEGER NOT NULL,
        historical_event INTEGER NOT NULL,
        threat_type      TEXT    NOT NULL
    )
""")

print("✓ Villages table created")

# =============================================
# INSERT VILLAGE DATA
# =============================================

# Clear existing data first so we don't duplicate
cursor.execute("DELETE FROM villages")

villages = [
    ("Kedarnath",        "Rudraprayag",   1200,   23,  0, 1, "BOTH"),
    ("Gangotri",         "Uttarkashi",    3400,   18,  0, 1, "BOTH"),
    ("Dharali",          "Uttarkashi",    2100,   31,  0, 1, "BOTH"),
    ("Joshimath",        "Chamoli",       16500,  41,  0, 1, "BOTH"),
    ("Raini",            "Chamoli",       450,    15,  0, 1, "BOTH"),
    ("Tapovan",          "Chamoli",       350,    12,  0, 1, "BOTH"),
    ("Govindghat",       "Chamoli",       800,    50,  0, 1, "BOTH"),
    ("Badrinath",        "Chamoli",       2800,   67,  1, 0, "GLOF"),
    ("Mana Village",     "Chamoli",       600,    72,  0, 0, "GLOF"),
    ("Munsiyari",        "Pithoragarh",   5200,   55,  1, 0, "GLOF"),
    ("Pithoragarh Town", "Pithoragarh",   12000,  120, 1, 0, "GLOF"),
    ("Uttarkashi Town",  "Uttarkashi",    8900,   45,  1, 1, "FLOOD"),
    ("Bhatwari",         "Uttarkashi",    3100,   60,  1, 0, "FLOOD"),
    ("Ghansali",         "Tehri Garhwal", 4200,   90,  1, 0, "FLOOD"),
    ("Haridwar",         "Haridwar",      228832, 999, 1, 0, "FLOOD"),
]

cursor.executemany("""
    INSERT INTO villages
        (name, district, population, travel_time,
         road_safe, historical_event, threat_type)
    VALUES (?, ?, ?, ?, ?, ?, ?)
""", villages)

print(f"✓ {len(villages)} villages inserted")

# =============================================
# VERIFY — show what's in the database
# =============================================

cursor.execute("SELECT id, name, district, population FROM villages")
rows = cursor.fetchall()

print("\n--- Villages in database ---")
for row in rows:
    print(f"  [{row[0]}] {row[1]:<20} {row[2]:<16} pop: {row[3]:,}")

