<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
</head>
<body>

<h1>AccessNav</h1>

<p>
AccessNav is a mobile navigation app built for wheelchair users and people
with mobility impairments. It finds wheelchair-accessible walking routes,
overlays turn-by-turn AR guidance, and lets the community report ramps,
elevators, and barriers in real time.
</p>

<p>
University project — Limassol, Cyprus.
</p>

<hr>

<h2>Features</h2>

<ul>
  <li>Email/password accounts with bcrypt-hashed passwords and persistent sessions</li>
  <li>Real-time GPS tracking with accuracy filtering and a desktop simulation mode</li>
  <li>Destination search powered by Nominatim, scoped to a local bounding box</li>
  <li>Accessibility map layer — ramps, elevators, and barriers from OpenStreetMap</li>
  <li>Wheelchair-accessible routing via OpenRouteService, with distance, ETA, and an accessibility score</li>
  <li>Colour-coded route polyline based on accessibility score</li>
  <li>AR turn-by-turn navigation — ground-anchored arrow, destination marker, and live HUD</li>
  <li>Community barrier reporting, submitted to a FastAPI backend and shown on the map</li>
  <li>Accessibility settings — high contrast mode, adjustable text size, voice navigation, and haptic feedback</li>
</ul>

<hr>

<h2>Tech stack</h2>

<table>
  <thead>
    <tr>
      <th>Layer</th>
      <th>Tools</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Mobile app</td>
      <td>Kivy 2.3.1, KivyMD 2.0, kivy-garden.mapview, Python 3.12</td>
    </tr>
    <tr>
      <td>Maps &amp; routing</td>
      <td>CartoDB Positron tiles, OpenStreetMap / Overpass API, OpenRouteService (wheelchair profile), Nominatim geocoding</td>
    </tr>
    <tr>
      <td>Augmented reality</td>
      <td>A-Frame, AR.js / WebXR, Android WebView, Kivy canvas simulation (desktop)</td>
    </tr>
    <tr>
      <td>Backend API</td>
      <td>FastAPI, Pydantic, Uvicorn, SQLite</td>
    </tr>
    <tr>
      <td>Auth &amp; security</td>
      <td>bcrypt, timing-safe login, session persistence</td>
    </tr>
    <tr>
      <td>Device services</td>
      <td>plyer (GPS, TTS, vibration, compass)</td>
    </tr>
    <tr>
      <td>Testing &amp; build</td>
      <td>pytest, httpx TestClient, buildozer (Android APK)</td>
    </tr>
  </tbody>
</table>

<hr>

<h2>Architecture</h2>

<pre>
Kivy / KivyMD app (Python 3.12)
  |
  |-- GPS Service        (plyer / desktop simulation)
  |-- Geocoding Service  (Nominatim search)
  |-- OSM Service        (Overpass accessibility data)
  |-- Routing Service    (OpenRouteService wheelchair profile)
  |
  |-- Map Screen    -&gt; MapView + RouteLayer + POI markers
  |-- AR Screen     -&gt; WebView (Android) / canvas simulation (desktop)
  |-- Report Screen -&gt; barrier submission form
  |
  v
FastAPI backend
  /register  /login  /spots  /report  /reports
  |
  v
SQLite database (users, spots, reports)
</pre>

<hr>

<h2>Setup</h2>

<h3>1. Clone the repo and create a virtual environment</h3>

<p>Requires Python 3.12.</p>

<pre>
git clone https://github.com/&lt;org&gt;/accessnav.git
cd accessnav
python -m venv venv
venv\Scripts\activate
</pre>

<h3>2. Install dependencies</h3>

<pre>
pip install -r requirements.txt

# MapView is installed separately from GitHub
pip install https://github.com/kivy-garden/mapview/archive/master.zip
</pre>

<h3>3. Configure environment variables</h3>

<p>Create a <code>.env</code> file in the project root:</p>

<pre>
ORS_API_KEY=your_openrouteservice_key
API_BASE_URL=http://localhost:8000
</pre>

<h3>4. Start the backend API</h3>

<p>Run this in its own terminal — the app talks to it over HTTP.</p>

<pre>
uvicorn api.main:app --reload --port 8000
</pre>

<p>Interactive docs available at <code>http://localhost:8000/docs</code>.</p>

<h3>5. Run the app</h3>

<pre>
python main.py
</pre>

<h3>6. Run the test suite</h3>

<pre>
pytest -v
</pre>

<h2>Team</h2>

<ul>
  <li>Kyriakos Girgis</li>
  <li>Romanos Neofytou</li>
  <li>Marios Avgousti</li>
</ul>

<hr>

<h2>License</h2>

<p>
Released under the MIT License. OpenStreetMap data is &copy; OpenStreetMap
contributors, available under the Open Database License. Map tiles courtesy
of CartoDB. Routing powered by OpenRouteService.
</p>

</body>
</html>
