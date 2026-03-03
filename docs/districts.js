<!DOCTYPE html>
<html lang="en">

  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Umbrella — Risk Map</title>

    <link rel="stylesheet"
      href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />

    <style>

      * { margin: 0; padding: 0; box-sizing: border-box; }

      body {
        background-color: #0a0f1e;
        color: #ffffff;
        font-family: Arial, sans-serif;
      }

      .navbar {
        background-color: #111827;
        padding: 16px 32px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-bottom: 2px solid #1e3a5f;
      }

      .logo {
        font-size: 24px;
        font-weight: bold;
        color: #38bdf8;
        letter-spacing: 2px;
      }

      .nav-links {
        display: flex;
        gap: 32px;
        list-style: none;
      }

      .nav-links a {
        color: #94a3b8;
        text-decoration: none;
        font-size: 14px;
        letter-spacing: 1px;
        text-transform: uppercase;
      }

      .nav-links a:hover { color: #38bdf8; }

      .page-header {
        padding: 16px 32px;
        border-bottom: 1px solid #1e3a5f;
        display: flex;
        align-items: center;
        justify-content: space-between;
      }

      .page-header h2 {
        font-size: 20px;
        color: #38bdf8;
        letter-spacing: 2px;
        text-transform: uppercase;
      }

      .page-header p {
        color: #94a3b8;
        font-size: 13px;
        margin-top: 4px;
      }

      .layer-controls {
        display: flex;
        gap: 12px;
        align-items: center;
      }

      .layer-btn {
        padding: 8px 16px;
        border-radius: 6px;
        border: 1px solid #1e3a5f;
        background-color: #1e293b;
        color: #94a3b8;
        font-size: 13px;
        cursor: pointer;
        letter-spacing: 1px;
        text-transform: uppercase;
      }

      .layer-btn.active {
        background-color: #38bdf8;
        color: #0a0f1e;
        font-weight: bold;
        border-color: #38bdf8;
      }

      .layer-btn:hover {
        border-color: #38bdf8;
        color: #38bdf8;
      }

      /* Live data status indicator */
      .data-status {
        font-size: 12px;
        padding: 6px 12px;
        border-radius: 20px;
        border: 1px solid #1e3a5f;
        color: #94a3b8;
        background-color: #1e293b;
      }

      .data-status.live {
        color: #22c55e;
        border-color: #22c55e;
        background-color: rgba(34,197,94,0.1);
      }

      .data-status.loading {
        color: #f97316;
        border-color: #f97316;
        background-color: rgba(249,115,22,0.1);
      }

      #map {
        height: calc(100vh - 150px);
        width: 100%;
      }

      .legend {
        background-color: #111827;
        border: 1px solid #1e3a5f;
        padding: 12px 16px;
        border-radius: 8px;
        font-size: 13px;
        line-height: 2;
        min-width: 180px;
      }

      .legend-title {
        font-weight: bold;
        color: #38bdf8;
        margin-bottom: 8px;
        letter-spacing: 1px;
        text-transform: uppercase;
        font-size: 11px;
      }

      .legend-item {
        display: flex;
        align-items: center;
        gap: 8px;
        color: #e2e8f0;
        font-size: 12px;
      }

      .dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        display: inline-block;
        flex-shrink: 0;
      }

      .swatch {
        width: 20px;
        height: 12px;
        display: inline-block;
        border-radius: 2px;
        flex-shrink: 0;
      }

    </style>

  </head>

  <body>

    <nav class="navbar">
      <div class="logo">☂ UMBRELLA</div>
      <ul class="nav-links">
        <li><a href="index.html">Home</a></li>
        <li><a href="map.html">Risk Map</a></li>
        <li><a href="vulnerability.html">Vulnerability Scorer</a></li>
        <li><a href="resources.html">Resource Recommender</a></li>
      </ul>
    </nav>

    <div class="page-header">
      <div>
        <h2>⚠ Live Hazard Risk Map</h2>
        <p>Uttarakhand — Glacial Lakes, Flood Zones & Live Rainfall</p>
      </div>
      <div class="layer-controls">

        <!-- Live data status badge -->
        <span class="data-status loading" id="data-status">
          ⏳ Fetching live rainfall...
        </span>

        <button class="layer-btn active" id="btn-glof"
          onclick="showLayer('glof')">
          ❄ GLOF Risk
        </button>
        <button class="layer-btn" id="btn-flood"
          onclick="showLayer('flood')">
          🌧 Flood Risk
        </button>
        <button class="layer-btn" id="btn-both"
          onclick="showLayer('both')">
          ⚡ Both
        </button>

      </div>
    </div>

    <div id="map"></div>

    <!-- Load districts data file first -->
    <script src="districts.js"></script>

    <!-- Then load Leaflet -->
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

    <script>

      // =============================================
      // 1. INITIALISE MAP
      // =============================================

      var map = L.map('map').setView([30.0668, 79.0193], 8);

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
      }).addTo(map);


      // =============================================
      // 2. GLACIAL LAKE MARKERS — same as before
      // =============================================

      var glacialLakes = [
        [30.7746, 79.0669, "Chorabari Lake",     "HIGH",   "Rudraprayag", "23 mins"],
        [30.4167, 79.9333, "Satopanth Lake",     "HIGH",   "Chamoli",     "41 mins"],
        [30.9167, 79.6500, "Vasuki Tal",         "MEDIUM", "Chamoli",     "67 mins"],
        [31.0167, 78.9833, "Dokriani Lake",      "HIGH",   "Uttarkashi",  "18 mins"],
        [30.5500, 80.2667, "Milam Glacier Lake", "MEDIUM", "Pithoragarh", "55 mins"],
        [30.8833, 79.7167, "Nandanvan Lake",     "MEDIUM", "Chamoli",     "72 mins"],
        [31.1000, 78.7500, "Kedartal Lake",      "HIGH",   "Uttarkashi",  "31 mins"],
        [30.3500, 79.6833, "Hemkund Lake",       "LOW",    "Chamoli",     "90 mins"]
      ];

      function getLakeColor(risk) {
        if (risk === "HIGH")   return "#ef4444";
        if (risk === "MEDIUM") return "#f97316";
        return "#22c55e";
      }

      var glofLayer = L.layerGroup();

      glacialLakes.forEach(function(lake) {
        var marker = L.circleMarker([lake[0], lake[1]], {
          radius:      10,
          fillColor:   getLakeColor(lake[3]),
          color:       "#ffffff",
          weight:      2,
          fillOpacity: 0.85
        });
        marker.bindPopup(
          "<b>" + lake[2] + "</b><br>" +
          "District: " + lake[4] + "<br>" +
          "Risk: <b style='color:" + getLakeColor(lake[3]) + "'>"
            + lake[3] + "</b><br>" +
          "Travel time to village: <b>" + lake[5] + "</b><br>" +
          "Hazard: Glacial Lake Outburst (GLOF)"
        );
        marker.addTo(glofLayer);
      });


      // =============================================
      // 3. FLOOD LAYER — now uses LIVE rainfall data
      // =============================================

      var floodLayer = L.layerGroup();

      // This function decides risk level from real mm data
      // Based on IMD's official flood guidance thresholds
      function getRainfallRisk(mm48hr) {
        if (mm48hr >= 115) return "HIGH";
        if (mm48hr >= 65)  return "MEDIUM";
        return "LOW";
      }

      function getFloodColor(risk) {
        if (risk === "HIGH")   return "#ef4444";
        if (risk === "MEDIUM") return "#f97316";
        return "#22c55e";
      }

      // Build Open-Meteo API URL for a single coordinate
      // past_days=2 gives us the last 48 hours of rainfall
      function buildRainfallURL(lat, lng) {
        return "https://api.open-meteo.com/v1/forecast" +
          "?latitude=" + lat +
          "&longitude=" + lng +
          "&daily=precipitation_sum" +
          "&past_days=2" +
          "&forecast_days=1" +
          "&timezone=Asia%2FKolkata";
      }

      // This stores rainfall results as they come in
      var rainfallResults = {};
      var fetchesCompleted = 0;

      // Fetch rainfall for ALL districts simultaneously
      // Promise.all means we wait for ALL fetches to finish
      // before drawing anything — so the map updates at once
      var allFetches = DISTRICTS.map(function(district) {

        var url = buildRainfallURL(district.lat, district.lng);

        return fetch(url)
          .then(function(response) {
            return response.json();
          })
          .then(function(data) {

            // Get the precipitation array
            var precipArray = data.daily.precipitation_sum;

            // Add up last 48 hours
            // precipArray has 3 values: [2 days ago, yesterday, today]
            // We want yesterday + today = 48hr total
            var mm48hr = precipArray[1] + precipArray[2];

            // Round to 1 decimal place
            mm48hr = Math.round(mm48hr * 10) / 10;

            // Store result against district name
            rainfallResults[district.name] = mm48hr;

            fetchesCompleted++;
            return { district: district, mm48hr: mm48hr };

          })
          .catch(function(error) {
            // If fetch fails for a district use 0mm as fallback
            console.log('Fetch failed for ' + district.name, error);
            rainfallResults[district.name] = 0;
            fetchesCompleted++;
            return { district: district, mm48hr: 0 };
          });

      });

      // When ALL district rainfall fetches are done
      Promise.all(allFetches).then(function(results) {

        // Draw flood zones with real data
        results.forEach(function(result) {

          var district = result.district;
          var mm48hr   = result.mm48hr;
          var risk     = getRainfallRisk(mm48hr);
          var color    = getFloodColor(risk);

          var polygon = L.polygon(district.coords, {
            color:       color,
            fillColor:   color,
            fillOpacity: 0.25,
            weight:      2
          });

          polygon.bindPopup(
            "<b>" + district.name + " District</b><br>" +
            "📡 <b>LIVE 48hr Rainfall: " + mm48hr + "mm</b><br>" +
            "Flood Risk: <b style='color:" + color + "'>" + risk + "</b><br>" +
            "At-risk Rivers: " + district.rivers + "<br>" +
            "<i style='color:#94a3b8;font-size:11px'>" +
            "IMD threshold: ≥115mm HIGH | 65–115mm MEDIUM</i>"
          );

          polygon.addTo(floodLayer);

        });

        // Update the status badge to show data is live
        var statusEl = document.getElementById('data-status');
        statusEl.innerText = '🟢 Live Rainfall Data';
        statusEl.classList.remove('loading');
        statusEl.classList.add('live');

        // Show GLOF layer by default
        glofLayer.addTo(map);

      });


      // =============================================
      // 4. LAYER CONTROL — same logic as before
      // =============================================

      glofLayer.addTo(map);

      function showLayer(type) {
        map.removeLayer(glofLayer);
        map.removeLayer(floodLayer);

        document.getElementById('btn-glof').classList.remove('active');
        document.getElementById('btn-flood').classList.remove('active');
        document.getElementById('btn-both').classList.remove('active');

        if (type === 'glof') {
          glofLayer.addTo(map);
          document.getElementById('btn-glof').classList.add('active');
        }
        if (type === 'flood') {
          floodLayer.addTo(map);
          document.getElementById('btn-flood').classList.add('active');
        }
        if (type === 'both') {
          glofLayer.addTo(map);
          floodLayer.addTo(map);
          document.getElementById('btn-both').classList.add('active');
        }
      }


      // =============================================
      // 5. LEGEND
      // =============================================

      var legend = L.control({ position: "bottomright" });

      legend.onAdd = function() {
        var div = L.DomUtil.create('div', 'legend');
        div.innerHTML =
          '<div class="legend-title">GLOF — Lake Risk</div>' +
          '<div class="legend-item">' +
            '<span class="dot" style="background:#ef4444"></span>' +
            ' High Risk' +
          '</div>' +
          '<div class="legend-item">' +
            '<span class="dot" style="background:#f97316"></span>' +
            ' Medium Risk' +
          '</div>' +
          '<div class="legend-item">' +
            '<span class="dot" style="background:#22c55e"></span>' +
            ' Low Risk' +
          '</div>' +
          '<br>' +
          '<div class="legend-title">Flood — Live Rainfall</div>' +
          '<div class="legend-item">' +
            '<span class="swatch" style="background:#ef4444;' +
            'opacity:0.6"></span> ≥115mm HIGH' +
          '</div>' +
          '<div class="legend-item">' +
            '<span class="swatch" style="background:#f97316;' +
            'opacity:0.6"></span> 65–115mm MED' +
          '</div>' +
          '<div class="legend-item">' +
            '<span class="swatch" style="background:#22c55e;' +
            'opacity:0.6"></span> &lt;65mm LOW' +
          '</div>';
        return div;
      };

      legend.addTo(map);

    </script>

  </body>

</html>