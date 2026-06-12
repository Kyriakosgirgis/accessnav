<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AccessNav — Wheelchair-Accessible Navigation</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root{
    --teal:#1D9E75;
    --teal-dark:#085041;
    --ink:#16231F;
    --ink-soft:#5B6B65;
    --paper:#F6F8F7;
    --card:#FFFFFF;
    --line:#E2E8E5;
    --amber:#E8A23A;
    --orange:#E3591F;
    --blue:#2278DE;
    --radius:14px;
  }

  *{margin:0;padding:0;box-sizing:border-box;}

  html{scroll-behavior:smooth;}

  body{
    font-family:'Inter',sans-serif;
    background:var(--paper);
    color:var(--ink);
    line-height:1.6;
    font-size:15.5px;
  }

  h1,h2,h3,h4{
    font-family:'Space Grotesk',sans-serif;
    letter-spacing:-0.01em;
    color:var(--ink);
  }

  code, .mono{
    font-family:'JetBrains Mono',monospace;
    font-size:0.85em;
  }

  a{color:var(--teal-dark);}

  /* ===================== HERO ===================== */
  .hero{
    background:linear-gradient(160deg,var(--teal) 0%, var(--teal-dark) 100%);
    color:#fff;
    padding:72px 24px 96px;
    position:relative;
    overflow:hidden;
  }
  .hero::after{
    content:"";
    position:absolute;
    right:-120px; top:-120px;
    width:380px; height:380px;
    border-radius:50%;
    border:1px solid rgba(255,255,255,0.14);
  }
  .hero::before{
    content:"";
    position:absolute;
    right:-40px; top:60px;
    width:240px; height:240px;
    border-radius:50%;
    border:1px solid rgba(255,255,255,0.10);
  }
  .hero-inner{max-width:920px; margin:0 auto; position:relative; z-index:2;}
  .eyebrow{
    display:inline-flex; align-items:center; gap:8px;
    font-family:'JetBrains Mono',monospace;
    font-size:12.5px; letter-spacing:0.12em; text-transform:uppercase;
    background:rgba(255,255,255,0.14);
    padding:6px 14px; border-radius:99px;
    margin-bottom:28px;
  }
  .eyebrow .dot{width:7px;height:7px;border-radius:50%;background:#A8FFD8;}
  .hero h1{
    font-size:54px; font-weight:700; line-height:1.08;
    max-width:760px; margin-bottom:18px;
  }
  .hero p.lead{
    font-size:18px; max-width:580px; color:rgba(255,255,255,0.88);
    margin-bottom:36px;
  }
  .hero-meta{display:flex; gap:28px; flex-wrap:wrap;}
  .hero-meta div{font-size:13px; color:rgba(255,255,255,0.7);}
  .hero-meta strong{display:block; font-family:'Space Grotesk',sans-serif; font-size:16px; color:#fff; font-weight:600;}
  .badges{display:flex; gap:8px; flex-wrap:wrap; margin-top:36px;}
  .badge{
    font-family:'JetBrains Mono',monospace; font-size:12px;
    background:rgba(255,255,255,0.12); border:1px solid rgba(255,255,255,0.18);
    padding:5px 12px; border-radius:99px; color:#fff;
  }

  /* ===================== LAYOUT ===================== */
  .layout{
    max-width:1180px; margin:0 auto;
    display:grid; grid-template-columns:240px 1fr;
    gap:56px;
    padding:56px 24px 120px;
  }

  /* ---- route sidebar nav ---- */
  .route-nav{position:sticky; top:32px; align-self:start;}
  .route-nav h4{
    font-size:11px; text-transform:uppercase; letter-spacing:0.14em;
    color:var(--ink-soft); margin-bottom:18px; font-weight:600;
  }
  .route-line{position:relative; padding-left:28px;}
  .route-line::before{
    content:""; position:absolute; left:7px; top:6px; bottom:6px;
    width:2px; background:var(--line); border-radius:2px;
  }
  .route-stop{position:relative; margin-bottom:6px;}
  .route-stop a{
    display:block; padding:7px 0; font-size:13.5px; color:var(--ink-soft);
    text-decoration:none; font-weight:500; transition:color .15s;
  }
  .route-stop a:hover{color:var(--teal-dark);}
  .route-stop::before{
    content:""; position:absolute; left:-28px; top:13px;
    width:13px; height:13px; border-radius:50%;
    background:#fff; border:2px solid var(--teal);
  }
  .route-stop.dest::before{ background:var(--orange); border-color:var(--orange); width:15px; height:15px; left:-29px; top:12px;}

  /* ===================== CONTENT ===================== */
  .content section{margin-bottom:64px; scroll-margin-top:32px;}
  .content h2{
    font-size:28px; font-weight:700; margin-bottom:6px;
    display:flex; align-items:center; gap:12px;
  }
  .section-tag{
    font-family:'JetBrains Mono',monospace; font-size:11px;
    color:var(--teal-dark); background:#E4F5EF; border-radius:6px;
    padding:3px 8px; letter-spacing:0.08em;
  }
  .content > section > p.kicker{
    color:var(--ink-soft); font-size:14px; margin-bottom:28px; max-width:640px;
  }

  /* feature grid */
  .grid{display:grid; grid-template-columns:repeat(2,1fr); gap:14px;}
  .card{
    background:var(--card); border:1px solid var(--line); border-radius:var(--radius);
    padding:20px 22px;
  }
  .card h3{font-size:15.5px; margin-bottom:6px; display:flex; align-items:center; gap:10px;}
  .card p{font-size:13.5px; color:var(--ink-soft);}
  .icon-chip{
    width:30px; height:30px; border-radius:9px; flex-shrink:0;
    display:flex; align-items:center; justify-content:center;
    font-size:15px; color:#fff;
  }

  /* tech stack table */
  .stack-table{width:100%; border-collapse:collapse; font-size:13.5px;}
  .stack-table th{
    text-align:left; font-family:'Space Grotesk',sans-serif; font-size:12px;
    text-transform:uppercase; letter-spacing:0.08em; color:var(--ink-soft);
    padding:0 14px 10px; border-bottom:1px solid var(--line);
  }
  .stack-table td{
    padding:11px 14px; border-bottom:1px solid var(--line); vertical-align:top;
  }
  .stack-table tr:last-child td{border-bottom:none;}
  .stack-table td:first-child{font-weight:600; white-space:nowrap; width:160px;}
  .pill{
    display:inline-block; font-family:'JetBrains Mono',monospace; font-size:11.5px;
    background:var(--paper); border:1px solid var(--line); border-radius:6px;
    padding:2px 7px; margin:2px 4px 2px 0; color:var(--ink);
  }

  /* architecture diagram */
  .arch{
    background:var(--card); border:1px solid var(--line); border-radius:var(--radius);
    padding:28px; display:flex; flex-direction:column; gap:0;
  }
  .arch-row{display:flex; gap:10px; align-items:stretch; flex-wrap:wrap;}
  .arch-box{
    flex:1; min-width:140px; background:var(--paper); border:1px solid var(--line);
    border-radius:10px; padding:14px 16px; font-size:13px;
  }
  .arch-box strong{display:block; font-family:'Space Grotesk',sans-serif; font-size:13.5px; margin-bottom:4px;}
  .arch-box span{color:var(--ink-soft); font-size:12px;}
  .arch-arrow{
    display:flex; align-items:center; justify-content:center;
    color:var(--ink-soft); font-size:18px; margin:6px 0;
  }
  .arch-box.accent{border-color:var(--teal); background:#F1FAF6;}

  /* setup steps */
  .steps{display:flex; flex-direction:column; gap:14px;}
  .step{
    display:grid; grid-template-columns:34px 1fr; gap:16px;
    background:var(--card); border:1px solid var(--line); border-radius:var(--radius);
    padding:18px 20px;
  }
  .step-num{
    width:34px; height:34px; border-radius:50%; background:var(--teal-dark);
    color:#fff; display:flex; align-items:center; justify-content:center;
    font-family:'Space Grotesk',sans-serif; font-weight:600; font-size:14px;
  }
  .step h4{font-size:14.5px; margin-bottom:6px;}
  .step p{font-size:13.5px; color:var(--ink-soft); margin-bottom:10px;}
  pre{
    background:#0F1A17; color:#D7F5E9; border-radius:10px; padding:14px 16px;
    font-family:'JetBrains Mono',monospace; font-size:12.5px; overflow-x:auto;
    line-height:1.7;
  }
  pre .c{color:#7FCBA4;}

  /* roadmap / status */
  .status-list{display:flex; flex-direction:column; gap:10px;}
  .status-item{
    display:grid; grid-template-columns:22px 130px 1fr 90px; align-items:center; gap:14px;
    background:var(--card); border:1px solid var(--line); border-radius:10px;
    padding:13px 16px; font-size:13.5px;
  }
  .status-dot{width:11px; height:11px; border-radius:50%;}
  .status-dot.done{background:var(--teal);}
  .status-dot.amber{background:var(--amber);}
  .status-item .name{font-weight:600;}
  .status-item .desc{color:var(--ink-soft); font-size:12.5px;}
  .status-pill{
    text-align:center; font-family:'JetBrains Mono',monospace; font-size:11px;
    padding:4px 10px; border-radius:99px; font-weight:600;
  }
  .status-pill.done{background:#E4F5EF; color:var(--teal-dark);}
  .status-pill.progress{background:#FCF1DD; color:#8A5A12;}

  /* team */
  .team-grid{display:grid; grid-template-columns:repeat(3,1fr); gap:14px;}
  .team-card{
    background:var(--card); border:1px solid var(--line); border-radius:var(--radius);
    padding:22px; text-align:center;
  }
  .avatar{
    width:52px; height:52px; border-radius:50%; margin:0 auto 12px;
    background:linear-gradient(135deg,var(--teal),var(--teal-dark));
    display:flex; align-items:center; justify-content:center;
    color:#fff; font-family:'Space Grotesk',sans-serif; font-weight:700; font-size:18px;
  }
  .team-card h4{font-size:14.5px; margin-bottom:2px;}
  .team-card span{font-size:12px; color:var(--ink-soft);}

  /* footer */
  .footer{
    border-top:1px solid var(--line); margin-top:40px; padding-top:28px;
    display:flex; justify-content:space-between; align-items:center;
    font-size:12.5px; color:var(--ink-soft); flex-wrap:wrap; gap:12px;
  }
  .footer .logo{
    font-family:'Space Grotesk',sans-serif; font-weight:700; color:var(--ink);
    display:flex; align-items:center; gap:8px;
  }
  .footer .logo .dot{width:9px;height:9px;border-radius:50%;background:var(--teal);}

  @media (max-width: 880px){
    .layout{grid-template-columns:1fr;}
    .route-nav{display:none;}
    .grid, .team-grid{grid-template-columns:1fr;}
    .hero h1{font-size:38px;}
    .status-item{grid-template-columns:18px 1fr; row-gap:4px;}
    .status-item .desc{grid-column:2; }
    .status-pill{grid-column:2; width:fit-content;}
  }
</style>
</head>
<body>

  <!-- ===================== HERO ===================== -->
  <header class="hero">
    <div class="hero-inner">
      <div class="eyebrow"><span class="dot"></span> University Project · Limassol, Cyprus</div>
      <h1>AccessNav — navigation that routes around the world's barriers, not through them.</h1>
      <p class="lead">
        A KivyMD mobile app that finds wheelchair-accessible walking routes,
        overlays turn-by-turn AR guidance, and lets the community map ramps,
        elevators, and obstacles in real time.
      </p>
      <div class="hero-meta">
        <div><strong>Kivy 2.3.1 · KivyMD 2.0</strong>Frontend framework</div>
        <div><strong>FastAPI · SQLite</strong>Backend &amp; storage</div>
        <div><strong>OpenRouteService</strong>Wheelchair routing engine</div>
        <div><strong>AR.js · A-Frame</strong>Augmented reality overlay</div>
      </div>
      <div class="badges">
        <span class="badge">python 3.12</span>
        <span class="badge">platform: android · desktop</span>
        <span class="badge">license: MIT</span>
        <span class="badge">status: in development</span>
      </div>
    </div>
  </header>

  <div class="layout">

    <!-- ===================== ROUTE SIDEBAR ===================== -->
    <nav class="route-nav">
      <h4>On this route</h4>
      <div class="route-line">
        <div class="route-stop"><a href="#about">Overview</a></div>
        <div class="route-stop"><a href="#features">Features</a></div>
        <div class="route-stop"><a href="#stack">Tech stack</a></div>
        <div class="route-stop"><a href="#architecture">Architecture</a></div>
        <div class="route-stop"><a href="#setup">Setup guide</a></div>
        <div class="route-stop"><a href="#status">Project status</a></div>
        <div class="route-stop"><a href="#team">Team</a></div>
        <div class="route-stop dest"><a href="#license">License</a></div>
      </div>
    </nav>

    <!-- ===================== CONTENT ===================== -->
    <main class="content">

      <!-- ABOUT -->
      <section id="about">
        <h2>Overview <span class="section-tag">01</span></h2>
        <p class="kicker">
          AccessNav is a mobile navigation app built for wheelchair users and
          people with mobility impairments. Instead of treating accessibility
          as an afterthought, every route is scored, every barrier is mapped,
          and every direction is delivered through voice, haptics, and an
          on-screen AR overlay.
        </p>
        <div class="grid">
          <div class="card">
            <h3><span class="icon-chip" style="background:var(--teal)">🗺</span> Live accessible maps</h3>
            <p>A clean CartoDB Positron basemap overlaid with colour-coded markers for ramps, elevators, and barriers — sourced from OpenStreetMap and the community.</p>
          </div>
          <div class="card">
            <h3><span class="icon-chip" style="background:var(--blue)">🧭</span> Wheelchair-first routing</h3>
            <p>Routes are calculated with OpenRouteService's wheelchair profile, returning distance, ETA, and an accessibility score for every journey.</p>
          </div>
          <div class="card">
            <h3><span class="icon-chip" style="background:var(--orange)">📡</span> AR turn-by-turn</h3>
            <p>A ground-anchored arrow, destination beacon, and live HUD guide users visually — with a desktop simulation and an Android AR.js/WebXR scene.</p>
          </div>
          <div class="card">
            <h3><span class="icon-chip" style="background:var(--teal-dark)">🚧</span> Community reporting</h3>
            <p>Users flag broken elevators, missing ramps, and blocked paths. Reports are reviewed and surfaced to everyone on the map.</p>
          </div>
        </div>
      </section>

      <!-- FEATURES -->
      <section id="features">
        <h2>Features <span class="section-tag">02</span></h2>
        <p class="kicker">Every screen in the app, end to end.</p>
        <div class="grid">
          <div class="card"><h3>🔐 Accounts</h3><p>Email/password registration and login with bcrypt-hashed passwords and persistent sessions.</p></div>
          <div class="card"><h3>📍 GPS tracking</h3><p>Real-time location with accuracy filtering and a desktop simulation mode for development.</p></div>
          <div class="card"><h3>🔎 Place search</h3><p>Debounced search powered by Nominatim, scoped to a configurable bounding box.</p></div>
          <div class="card"><h3>♿ Accessibility layer</h3><p>Toggleable ramp, elevator, and barrier markers pulled from OpenStreetMap's Overpass API.</p></div>
          <div class="card"><h3>🧮 Route scoring</h3><p>Each route returns a distance, ETA, and a 0–1 accessibility score rendered as a coloured polyline.</p></div>
          <div class="card"><h3>🥽 AR navigation</h3><p>Ground-plane directional arrow, spinning destination ring, and a live distance/ETA HUD.</p></div>
          <div class="card"><h3>📝 Barrier reports</h3><p>In-app form to flag obstacles by type and description, submitted directly to the backend.</p></div>
          <div class="card"><h3>⚙️ Accessibility settings</h3><p>High-contrast theme, adjustable text size, voice navigation, and haptic feedback toggles.</p></div>
        </div>
      </section>

      <!-- TECH STACK -->
      <section id="stack">
        <h2>Tech stack <span class="section-tag">03</span></h2>
        <p class="kicker">What's running under the hood.</p>
        <table class="stack-table">
          <tr><th>Layer</th><th>Tools</th></tr>
          <tr>
            <td>Mobile app</td>
            <td>
              <span class="pill">Kivy 2.3.1</span>
              <span class="pill">KivyMD 2.0</span>
              <span class="pill">kivy-garden.mapview</span>
              <span class="pill">Python 3.12</span>
            </td>
          </tr>
          <tr>
            <td>Maps &amp; routing</td>
            <td>
              <span class="pill">CartoDB Positron tiles</span>
              <span class="pill">OpenStreetMap / Overpass API</span>
              <span class="pill">OpenRouteService (wheelchair profile)</span>
              <span class="pill">Nominatim geocoding</span>
            </td>
          </tr>
          <tr>
            <td>Augmented reality</td>
            <td>
              <span class="pill">A-Frame</span>
              <span class="pill">AR.js / WebXR</span>
              <span class="pill">Android WebView</span>
              <span class="pill">Kivy canvas simulation</span>
            </td>
          </tr>
          <tr>
            <td>Backend API</td>
            <td>
              <span class="pill">FastAPI</span>
              <span class="pill">Pydantic</span>
              <span class="pill">Uvicorn</span>
              <span class="pill">SQLite</span>
            </td>
          </tr>
          <tr>
            <td>Auth &amp; security</td>
            <td>
              <span class="pill">bcrypt</span>
              <span class="pill">timing-safe login</span>
              <span class="pill">session persistence</span>
            </td>
          </tr>
          <tr>
            <td>Device services</td>
            <td>
              <span class="pill">plyer (GPS)</span>
              <span class="pill">plyer (TTS)</span>
              <span class="pill">plyer (vibration)</span>
              <span class="pill">plyer (compass)</span>
            </td>
          </tr>
          <tr>
            <td>Testing &amp; build</td>
            <td>
              <span class="pill">pytest</span>
              <span class="pill">httpx TestClient</span>
              <span class="pill">buildozer (Android APK)</span>
            </td>
          </tr>
        </table>
      </section>

      <!-- ARCHITECTURE -->
      <section id="architecture">
        <h2>Architecture <span class="section-tag">04</span></h2>
        <p class="kicker">High-level data flow from the app to external services.</p>
        <div class="arch">
          <div class="arch-row">
            <div class="arch-box accent"><strong>Kivy / KivyMD app</strong><span>Screens, services, components — Python 3.12</span></div>
          </div>
          <div class="arch-arrow">↓</div>
          <div class="arch-row">
            <div class="arch-box"><strong>GPS Service</strong><span>plyer / desktop sim</span></div>
            <div class="arch-box"><strong>Geocoding Service</strong><span>Nominatim search</span></div>
            <div class="arch-box"><strong>OSM Service</strong><span>Overpass accessibility data</span></div>
            <div class="arch-box"><strong>Routing Service</strong><span>OpenRouteService wheelchair API</span></div>
          </div>
          <div class="arch-arrow">↓</div>
          <div class="arch-row">
            <div class="arch-box"><strong>Map Screen</strong><span>MapView + RouteLayer + POI markers</span></div>
            <div class="arch-box"><strong>AR Screen</strong><span>WebView (Android) / canvas sim (desktop)</span></div>
            <div class="arch-box"><strong>Report Screen</strong><span>Barrier submission form</span></div>
          </div>
          <div class="arch-arrow">↓</div>
          <div class="arch-row">
            <div class="arch-box accent"><strong>FastAPI backend</strong><span>/register · /login · /spots · /report · /reports</span></div>
          </div>
          <div class="arch-arrow">↓</div>
          <div class="arch-row">
            <div class="arch-box"><strong>SQLite database</strong><span>users · spots · reports</span></div>
          </div>
        </div>
      </section>

      <!-- SETUP -->
      <section id="setup">
        <h2>Setup guide <span class="section-tag">05</span></h2>
        <p class="kicker">Get the app and API running locally.</p>
        <div class="steps">
          <div class="step">
            <div class="step-num">1</div>
            <div>
              <h4>Clone &amp; create a virtual environment</h4>
              <p>Python 3.12 is required.</p>
              <pre>git clone https://github.com/&lt;org&gt;/accessnav.git
<span class="c"># Windows</span>
cd accessnav
python -m venv venv
venv\Scripts\activate</pre>
            </div>
          </div>
          <div class="step">
            <div class="step-num">2</div>
            <div>
              <h4>Install dependencies</h4>
              <p>Installs Kivy, KivyMD, FastAPI, routing, and device-service libraries.</p>
              <pre>pip install -r requirements.txt
<span class="c"># MapView is installed separately from GitHub</span>
pip install https://github.com/kivy-garden/mapview/archive/master.zip</pre>
            </div>
          </div>
          <div class="step">
            <div class="step-num">3</div>
            <div>
              <h4>Configure environment variables</h4>
              <p>Create a <code>.env</code> file in the project root.</p>
              <pre>ORS_API_KEY=your_openrouteservice_key
API_BASE_URL=http://localhost:8000</pre>
            </div>
          </div>
          <div class="step">
            <div class="step-num">4</div>
            <div>
              <h4>Start the backend API</h4>
              <p>Run this in its own terminal — the app talks to it over HTTP.</p>
              <pre>uvicorn api.main:app --reload --port 8000
<span class="c"># Docs available at http://localhost:8000/docs</span></pre>
            </div>
          </div>
          <div class="step">
            <div class="step-num">5</div>
            <div>
              <h4>Run the app</h4>
              <p>Launches the KivyMD desktop build with GPS simulation enabled.</p>
              <pre>python main.py</pre>
            </div>
          </div>
          <div class="step">
            <div class="step-num">6</div>
            <div>
              <h4>Run the test suite</h4>
              <p>Covers authentication, routing, and the FastAPI endpoints.</p>
              <pre>pytest -v</pre>
            </div>
          </div>
        </div>
      </section>

      <!-- STATUS -->
      <section id="status">
        <h2>Project status <span class="section-tag">06</span></h2>
        <p class="kicker">Where each part of the build currently stands.</p>
        <div class="status-list">
          <div class="status-item"><div class="status-dot done"></div><div class="name">Auth &amp; sessions</div><div class="desc">bcrypt login/register, persistent sessions, route guards</div><div class="status-pill done">Complete</div></div>
          <div class="status-item"><div class="status-dot done"></div><div class="name">Map &amp; GPS</div><div class="desc">Live location, search, accessibility POI layer</div><div class="status-pill done">Complete</div></div>
          <div class="status-item"><div class="status-dot done"></div><div class="name">Routing</div><div class="desc">ORS wheelchair profile, scored polylines, route info card</div><div class="status-pill done">Complete</div></div>
          <div class="status-item"><div class="status-dot done"></div><div class="name">AR navigation</div><div class="desc">Desktop simulation complete; Android WebView scene wired</div><div class="status-pill done">Complete</div></div>
          <div class="status-item"><div class="status-dot done"></div><div class="name">Backend &amp; reports</div><div class="desc">FastAPI endpoints live, community layer on map</div><div class="status-pill done">Complete</div></div>
          <div class="status-item"><div class="status-dot amber"></div><div class="name">Settings &amp; polish</div><div class="desc">Accessibility settings done; error handling &amp; docs in progress</div><div class="status-pill progress">In progress</div></div>
          <div class="status-item"><div class="status-dot amber"></div><div class="name">Testing &amp; APK</div><div class="desc">API tests passing; routing/GPS tests and Android build remaining</div><div class="status-pill progress">In progress</div></div>
        </div>
      </section>

      <!-- TEAM -->
      <section id="team">
        <h2>Team <span class="section-tag">07</span></h2>
        <p class="kicker">Built by three students in Limassol, Cyprus.</p>
        <div class="team-grid">
          <div class="team-card">
            <div class="avatar">KG</div>
            <h4>Kyriakos Girgis</h4>
            <span>Developer</span>
          </div>
          <div class="team-card">
            <div class="avatar">RN</div>
            <h4>Romanos Neofytou</h4>
            <span>Developer</span>
          </div>
          <div class="team-card">
            <div class="avatar">MA</div>
            <h4>Marios Avgousti</h4>
            <span>Developer</span>
          </div>
        </div>
      </section>

      <!-- LICENSE -->
      <section id="license">
        <h2>License <span class="section-tag">08</span></h2>
        <p class="kicker">
          Released under the MIT License. OpenStreetMap data is © OpenStreetMap
          contributors and available under the Open Database License. Map tiles
          courtesy of CartoDB. Routing powered by OpenRouteService.
        </p>
        <div class="footer">
          <div class="logo"><span class="dot"></span> AccessNav</div>
          <div>University Project · Cyprus · 2025–2026</div>
        </div>
      </section>

    </main>
  </div>

</body>
</html>
