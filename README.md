# ☂ UMBRELLA
### Multi-Hazard Early Warning & Response Dashboard
**Uttarakhand Disaster Intelligence System**

---

## 🌐 Live Links

| | URL |
|---|---|
| **🖥 Live Dashboard** | [anubhavpadiyar.github.io/umbrella](https://anubhavpadiyar.github.io/umbrella) |
| **🗺 Risk Map** | [anubhavpadiyar.github.io/umbrella/map.html](https://anubhavpadiyar.github.io/umbrella/map.html) |
| **🏘 Vulnerability Scorer** | [anubhavpadiyar.github.io/umbrella/vulnerability.html](https://anubhavpadiyar.github.io/umbrella/vulnerability.html) |
| **⚡ Resource Recommender** | [anubhavpadiyar.github.io/umbrella/resources.html](https://anubhavpadiyar.github.io/umbrella/resources.html) |
| **🌍 Seismic Monitor** | [anubhavpadiyar.github.io/umbrella/earthquake.html](https://anubhavpadiyar.github.io/umbrella/earthquake.html) |
| **🔥 Forest Fire Monitor** | [anubhavpadiyar.github.io/umbrella/fire.html](https://anubhavpadiyar.github.io/umbrella/fire.html) |
| **🌊 Dam Risk** | [anubhavpadiyar.github.io/umbrella/dam.html](https://anubhavpadiyar.github.io/umbrella/dam.html) |
| **💧 River Monitor** | [anubhavpadiyar.github.io/umbrella/river.html](https://anubhavpadiyar.github.io/umbrella/river.html) |
| **📋 Incident Log** | [anubhavpadiyar.github.io/umbrella/incidents.html](https://anubhavpadiyar.github.io/umbrella/incidents.html) |
| **📄 PDF Situation Report** | [anubhavpadiyar.github.io/umbrella/report.html](https://anubhavpadiyar.github.io/umbrella/report.html) |
| **🔌 Backend API** | [umbrella-0a7v.onrender.com](https://umbrella-0a7v.onrender.com) |

---

## The Problem

In June 2013, over 6,000 people died in the Kedarnath disaster. In February 2021, a glacial lake outburst in Chamoli's Tapovan killed 200 more. Both events shared a critical failure — **ground-level intelligence arrived too late.**

Weather alerts exist. What doesn't exist is a tool that tells a District Magistrate at 11pm: *which villages are at risk right now, which roads are still open, how many minutes until the flood front arrives, and exactly which NDRF teams to deploy where.*

Umbrella fills that gap.

---

## What Umbrella Does

A full-stack multi-hazard disaster intelligence platform built for district-level emergency response in the Uttarakhand Himalayan Region. Five live data sources. Eight hazard modules. One unified dashboard.

### 🌧 Flood & GLOF Risk
- 8 real glacial lake markers with GLOF travel times to nearest villages
- Live flood risk zones for 6 districts — updated on every page load
- Real 48hr cumulative rainfall from Open-Meteo API
- IMD threshold classification: ≥115mm HIGH · 65–115mm MEDIUM · <65mm LOW

### 🏘 Village Vulnerability Scorer
- 15 real Uttarakhand villages scored using the NDMA Risk Framework
- Scores driven by **live rainfall data** — not hardcoded values
- Formula: Hazard (50pts) + Vulnerability (30pts) + Exposure (20pts)
- Seasonal population multiplier — Char Dham pilgrim villages get 30x population during May–November
- Filter by risk level, threat type, district

### 🌍 Seismic Monitor
- Live earthquake feed from USGS Earthquake Hazards Program
- M2.5+ detections within 350km of Uttarakhand
- Village seismic zone classification (Zone III / IV / V) per BIS IS 1893
- Haversine distance from each quake epicenter to nearest village

### 🔥 Forest Fire Monitor
- Live active fire detections from NASA FIRMS (VIIRS SNPP satellite)
- 375m resolution, updated every 3 hours
- Village fire risk scored by proximity to active fires + forest cover %
- Forest cover data from Forest Survey of India 2021

### 🌊 Dam Risk Module
- 5 major dams: Tehri, Maneri Bhali, Vishnu Prayag, Srinagar, Koteshwar
- Structural risk assessment: height, capacity, seismic zone, age
- Downstream impact zones with estimated flood travel times
- Population at risk per downstream settlement

### 💧 River Discharge Monitor
- Live discharge data for 7 Himalayan rivers from Open-Meteo Flood API
- Bhagirathi · Alaknanda · Mandakini · Pindar · Kali · Yamuna · Tons
- 7-day average and peak discharge
- Classified against historical flood thresholds per river

### 🗺 Live Hazard Risk Map
- 5 layer toggles: GLOF · Flood · Both · Seismic · Forest Fire
- Seismic layer: village markers colored by zone (red=V, orange=IV, green=III)
- Fire layer: NASA FIRMS hotspots plotted in real time

### ⚡ Resource Recommender
- NDRF, SDRF, helicopter and hospital status tracking
- District-level action checklists with P1/P2/P3 priority
- WhatsApp alert generator in English and Hindi

### 📋 Incident Log
- Persistent backend storage — saved to SQLite, not browser localStorage
- Manual decision logging (NDRF deployed, evacuation ordered, etc.)
- Auto-detects risk level changes and logs them automatically
- Timestamped feed, filterable by manual / auto entries

### 📄 PDF Situation Report
- One-click situation report generated from live data
- Includes: risk summary, village scores table, rainfall status, recommended actions
- Formatted for government use — downloadable as PDF

### 📰 Live Disaster News
- Live Uttarakhand disaster and weather news from NewsData.io
- Floods, landslides, fires, earthquakes, snowfall — updated on every load

### ⚙ Admin Panel
- Password-protected
- Add, edit, delete villages directly from browser
- Auto-migrates database schema on deployment

---

## Architecture

```
Browser (HTML · CSS · JavaScript)
         ↕  JSON over HTTP
Flask API Server — Render
    ↕           ↕           ↕           ↕
SQLite DB   Open-Meteo   USGS API   NASA FIRMS
(villages   (rainfall +  (quakes)    (fires)
+incidents)  flood)
```

**Frontend:** HTML5 · CSS3 · JavaScript · Leaflet.js — hosted on GitHub Pages  
**Backend:** Python · Flask · Flask-CORS — hosted on Render  
**Database:** SQLite  
**Data Sources:** Open-Meteo API · USGS Earthquake Hazards Program · NASA FIRMS · NewsData.io · ISRO NRSC

---

## Hazard Coverage

| Module | Status | Data Source |
|--------|--------|-------------|
| GLOF (Glacial Lake Outburst) | ✅ Live | ISRO NRSC coordinates |
| Monsoon Flooding | ✅ Live | Open-Meteo API |
| Earthquake / Seismic | ✅ Live | USGS Earthquake Hazards Program |
| Forest Fire | ✅ Live | NASA FIRMS VIIRS SNPP |
| Dam Risk | ✅ Static + Seismic | CWC India data |
| River Discharge | ✅ Live | Open-Meteo Flood API |
| Avalanche | 🔄 Planned | SRTM DEM + IMD snowpack |
| Tehri Dam Live Level | 🔄 Planned | CWC live gauge |

---

## Districts Monitored

Uttarkashi · Chamoli · Rudraprayag · Tehri Garhwal · Pithoragarh · Haridwar

---

## Running Locally

```bash
git clone https://github.com/AnubhavPadiyar/umbrella.git
cd umbrella
pip install flask flask-cors certifi
python3 setup_db.py
python3 server.py
```

Server runs at `http://localhost:5001`. Open `index.html` in your browser.

---

## Vulnerability Scoring Formula — NDMA Framework

### Hazard (50pts — dynamic)

| Factor | Max | Scoring |
|--------|-----|---------|
| Live Rainfall (48hr) | 30pts | ≥115mm=30 · 65–115mm=18 · <65mm=6 |
| GLOF Travel Time | 20pts | <20min=20 · <40=15 · <60=10 · <90=5 |

### Vulnerability (30pts — permanent)

| Factor | Max | Scoring |
|--------|-----|---------|
| Road Access Routes | 15pts | 1 route=15 · 2 routes=8 · 3+ routes=0 |
| Historical Event | 15pts | Yes=15 · No=0 |

### Exposure (20pts)

| Factor | Max | Scoring |
|--------|-----|---------|
| Population | 20pts | >10k=20 · >5k=16 · >1k=12 · >500=8 · ≤500=4 |

**Note:** Pilgrimage villages (Kedarnath, Badrinath, Gangotri etc.) use 30x population multiplier during May–November (Char Dham season).

**Risk Classification:** ≥70 = HIGH · 45–69 = MEDIUM · <45 = LOW

---

## Formula Validation — Kedarnath 2013 Backtest

| Factor | 2013 Conditions | Score |
|--------|----------------|-------|
| Live Rainfall | 185mm — HIGH (≥115mm) | 30pts |
| GLOF Travel Time | 23 minutes from Chorabari Lake | 15pts |
| Road Access | 1 route (trekking only) | 15pts |
| Historical Event | Yes — prior flood history | 15pts |
| Population | 1,200 permanent residents | 8pts |
| **Total Score** | | **83 / 100 — HIGH ✅** |

**Known Limitation:** Formula uses permanent population. During Char Dham season, Kedarnath hosts 40,000–50,000 pilgrims. Seasonal multiplier now implemented.

---

## Roadmap

- [ ] Mobile responsive design
- [ ] CWC live river gauge integration
- [ ] Tehri Dam live reservoir level
- [ ] Himachal Pradesh expansion
- [ ] SMS/WhatsApp alert gateway
- [ ] Auto-refresh every 15 minutes
- [ ] Avalanche module

---

## Built By

**Anubhav Padiyar** — B.Tech Computer Science and Engineering

GitHub: [github.com/AnubhavPadiyar](https://github.com/AnubhavPadiyar)  
LinkedIn: [linkedin.com/in/anubhav-padiyar-b9235237b](https://www.linkedin.com/in/anubhav-padiyar-b9235237b)  
Email: anubhavpadiyar@gmail.com

---
