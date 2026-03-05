# migrate_db.py
# Run this ONCE to upgrade existing umbrella.db
# Changes road_safe (boolean) → road_access (integer: 1/2/3)
# Safe to run — does not delete any village data

import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "umbrella.db")
conn   = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if migration already done
cursor.execute("PRAGMA table_info(villages)")
columns = [row[1] for row in cursor.fetchall()]

if "road_access" in columns:
    print("✓ Already migrated — road_access column exists")
    conn.close()
    exit()

print("Starting migration: road_safe → road_access")

# Step 1: Add new column
cursor.execute("ALTER TABLE villages ADD COLUMN road_access INTEGER NOT NULL DEFAULT 1")
print("✓ Added road_access column")

# Step 2: Set road_access values based on known geography
# Villages with road_safe=1 (was safe) get 2 routes as default
# Villages with road_safe=0 (was blocked) keep 1 route
cursor.execute("UPDATE villages SET road_access = 1 WHERE road_safe = 0")
cursor.execute("UPDATE villages SET road_access = 2 WHERE road_safe = 1")
print("✓ Set initial road_access values from road_safe")

# Step 3: Apply correct geographic values for known villages
road_access_map = {
    "Kedarnath":        1,
    "Gangotri":         1,
    "Dharali":          1,
    "Joshimath":        1,
    "Raini":            1,
    "Tapovan":          1,
    "Govindghat":       1,
    "Badrinath":        1,
    "Mana Village":     1,
    "Munsiyari":        2,
    "Pithoragarh Town": 3,
    "Uttarkashi Town":  2,
    "Bhatwari":         2,
    "Ghansali":         2,
    "Haridwar":         3,
}

for name, routes in road_access_map.items():
    cursor.execute("UPDATE villages SET road_access = ? WHERE name = ?", (routes, name))

print("✓ Applied correct geographic road_access values")

conn.commit()

# Verify
cursor.execute("SELECT name, road_access FROM villages ORDER BY id")
rows = cursor.fetchall()
print("\n--- Road access after migration ---")
for row in rows:
    label = "1 route" if row[1]==1 else f"{row[1]} routes"
    print(f"  {row[0]:<22} {label}")

conn.close()
print("\n✓ Migration complete")
print("  You can now remove the road_safe column (optional)")
print("  Next: replace brain.py and server.py with new versions")
