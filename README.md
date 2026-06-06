# 🎵 World Instruments Explorer

An interactive world map app to discover traditional instruments from 90+ countries, play audio samples, and send them directly into [Audiotool](https://audiotool.com) as playable instruments.

---

## 🚀 Running Locally

### Prerequisites
- Python 3.8+ ([download](https://python.org))
- Node.js (only needed to rebuild the Audiotool SDK bundle — see below)

### Setup & Start

**Mac / Linux:**
```bash
chmod +x start.sh
./start.sh
```

**Windows:**
```
start.bat
```

**Or manually:**
```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Then open **`index.html`** via a local HTTP server (see note below).

> **Important:** Open `index.html` via HTTP, not `file://`. The easiest way is [VS Code Live Server](https://marketplace.visualstudio.com/items?itemName=ritwickdey.LiveServer) (`http://127.0.0.1:5500/`) or the FastAPI backend (`http://localhost:8000/`). The Audiotool OAuth integration requires a real HTTP origin.

---

## 🎹 Audiotool Integration Setup

Each instrument card has a **"Use as Instrument"** button that uploads the sample to Audiotool and creates a Machiniste device in your project.

### 1. Build the Audiotool SDK bundle

The SDK bundle (`audiotool-nexus.js`) is not included in the repo. Build it once:

```bash
npm install @audiotool/nexus@0.0.17 esbuild --save-dev
npx esbuild --bundle --format=esm --platform=browser node_modules/@audiotool/nexus/dist/index.js --outfile=audiotool-nexus.js
# Patch the browser Wasm guard:
sed -i 's/if (typeof process < "u")/if (false) \/\/ patched: browser build/' audiotool-nexus.js
```

Place `audiotool-nexus.js` in the same folder as `index.html`.

### 2. Register an Audiotool app

Go to [developer.audiotool.com/applications](https://developer.audiotool.com/applications) and create an app with:
- **Redirect URI:** `http://127.0.0.1:5500/` (or wherever you serve `index.html`)
- **Scope:** `project:write samples:write`

### 3. Configure in the app

Click **🎹 Audiotool** in the top-right header and enter:
- Your **Client ID** from the developer portal
- Your **Project URL** from `beta.audiotool.com` (e.g. `https://beta.audiotool.com/studio?project=...`)
- The **Redirect URI** matching your app registration

---

## 🎵 Audio Samples

Audio samples are included in the repo. 

This fetches CC-licensed samples from Freesound.org into the `audio/` folder. You'll need a [Freesound API key](https://freesound.org/apiv2/apply/).

---

## 📁 Project Structure

```
world_instruments_explorer/
├── index.html           # Frontend — interactive world map + 3D globe + Audiotool integration
├── main.py              # FastAPI backend with REST endpoints
├── models.py            # All data: 90+ countries, instruments, audio URLs
├── download_audio.py    # Downloads CC audio samples from Freesound.org
├── requirements.txt     # Python dependencies
├── start.sh             # Quick-start script (Mac/Linux)
├── start.bat            # Quick-start script (Windows)
├── audio/               # Local audio files (not in repo — run download_audio.py)
└── audiotool-nexus.js   # Audiotool SDK bundle (not in repo — build with esbuild)
```

---

## 🗺️ Features

- **Flat map** and **3D rotating globe** views
- Click any country to see its traditional instruments
- ▶️ Play audio samples (CC licensed, from Wikimedia Commons + Freesound)
- 🎹 Send any instrument to [Audiotool](https://audiotool.com) as a playable Machiniste instrument
- 90+ countries, 437 instruments

---

## 🔌 API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/` | API summary |
| GET | `/countries` | All countries |
| GET | `/countries/{country}` | Country detail + audio URLs |
| GET | `/regions` | All regions |
| GET | `/regions/{region}` | Countries in a region |
| GET | `/instruments` | All instruments (`?audio_only=true`) |
| GET | `/instruments/search?q=...` | Search by name/description |
| GET | `/audio` | All audio samples |
| GET | `/audio/{key}` | Specific audio URL |

Interactive docs: **http://localhost:8000/docs**
