# 🎵 World Instruments Explorer

An interactive world map app to discover traditional instruments from 90+ countries and play audio samples.

---

## 🚀 Running Locally

### Prerequisites
- Python 3.8+ ([download](https://python.org))

### Setup & Start

**Mac / Linux:**
```bash
cd world_instruments_explorer
chmod +x start.sh
./start.sh
```

**Windows:**
```
cd world_instruments_explorer
start.bat
```

**Or manually:**
```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Then open **`index.html`** in your browser (just double-click it, or drag it into Chrome/Firefox).

> **Note:** The HTML frontend works standalone — instrument data is embedded in its JS. The API is optional, for building on top of the project.

---

## 📁 Project Structure

```
world_instruments_explorer/
├── index.html       # Frontend — interactive world map + 3D globe
├── main.py          # FastAPI backend with REST endpoints
├── models.py        # All data: 90+ countries, instruments, audio URLs
├── requirements.txt # Python dependencies
├── start.sh         # Quick-start script (Mac/Linux)
├── start.bat        # Quick-start script (Windows)
└── README.md
```

---

## 🗺️ Features

- **Flat map** and **3D rotating globe** views
- Click any country to see its traditional instruments
- ▶️ Play audio samples (CC licensed, from Wikimedia Commons)
- 90+ countries covered across all world regions

---

## 🔌 API Endpoints (optional)

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

---

## Example API calls

```bash
curl http://localhost:8000/countries/Japan
curl http://localhost:8000/instruments?audio_only=true
curl "http://localhost:8000/instruments/search?q=drum"
```
