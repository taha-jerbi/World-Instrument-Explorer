"""
World Instruments Explorer — FastAPI Backend
============================================
Çalıştırmak için:
    pip install fastapi uvicorn
    uvicorn main:app --reload

Audio files:
    Drop your .mp3 / .ogg / .wav files into the  audio/  folder.
    Name them exactly like the key in models.py  (e.g. tabla.mp3, oud.ogg).
    The backend will serve them at  GET /audio/{key}/file
    and return that local URL automatically — no CORS issues.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from typing import Optional
from models import AUDIO, DATA

AUDIO_DIR = Path(__file__).parent / "audio"
AUDIO_DIR.mkdir(exist_ok=True)

SUPPORTED_EXTENSIONS = [".mp3", ".ogg", ".wav", ".m4a", ".flac"]

app = FastAPI(
    title="World Instruments Explorer API",
    description="Ülkelere göre geleneksel müzik aletleri ve ses kayıtları.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Serve the audio folder as static files too (optional direct access)
app.mount("/audio-files", StaticFiles(directory=str(AUDIO_DIR)), name="audio-files")


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def find_local_audio(key: str) -> Optional[Path]:
    """Return the path of a local audio file matching the key, or None."""
    for ext in SUPPORTED_EXTENSIONS:
        candidate = AUDIO_DIR / f"{key}{ext}"
        if candidate.exists():
            return candidate
    return None


def resolve_audio_url(key: str, base_url: str = "http://localhost:8000") -> Optional[str]:
    """
    Priority:
      1. Local file in audio/ folder  →  served via /audio/{key}/file
      2. URL in models.py AUDIO dict  →  returned as-is
      3. None
    """
    if find_local_audio(key):
        return f"{base_url}/audio/{key}/file"
    return AUDIO.get(key)


# ─────────────────────────────────────────────────────────────────────────────
# ROOT
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    local_files = [p.stem for ext in SUPPORTED_EXTENSIONS for p in AUDIO_DIR.glob(f"*{ext}")]
    return {
        "name": "World Instruments Explorer API",
        "version": "2.0.0",
        "countries": len(DATA),
        "audio_samples_in_models": len(AUDIO),
        "local_audio_files": sorted(set(local_files)),
        "endpoints": [
            "/countries",
            "/countries/{country}",
            "/regions",
            "/regions/{region}",
            "/instruments?audio_only=false",
            "/instruments/search?q=...",
            "/audio",
            "/audio/{key}",
            "/audio/{key}/file  ← streams local file",
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# AUDIO — file streaming endpoint
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/audio/{key}/file")
def stream_audio_file(key: str):
    """Stream a local audio file from the audio/ folder."""
    path = find_local_audio(key.lower())
    if not path:
        raise HTTPException(
            status_code=404,
            detail=f"No local audio file found for '{key}'. "
                   f"Drop a file named '{key}.mp3' (or .ogg/.wav) into the audio/ folder."
        )
    media_types = {
        ".mp3": "audio/mpeg",
        ".ogg": "audio/ogg",
        ".wav": "audio/wav",
        ".m4a": "audio/mp4",
        ".flac": "audio/flac",
    }
    media_type = media_types.get(path.suffix, "audio/mpeg")
    return FileResponse(path, media_type=media_type, headers={"Accept-Ranges": "bytes"})


# ─────────────────────────────────────────────────────────────────────────────
# AUDIO — metadata endpoints
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/audio")
def list_audio():
    """List all audio samples. Local files take priority over Wikimedia URLs."""
    local_files = {p.stem for ext in SUPPORTED_EXTENSIONS for p in AUDIO_DIR.glob(f"*{ext}")}
    all_keys = sorted(set(list(AUDIO.keys()) + list(local_files)))
    result = []
    for key in all_keys:
        local = key in local_files
        url = f"http://localhost:8000/audio/{key}/file" if local else AUDIO.get(key)
        result.append({"key": key, "url": url, "source": "local" if local else "wikimedia"})
    return result


@app.get("/audio/{key}")
def get_audio(key: str):
    """Return the best available audio URL for an instrument key."""
    key = key.lower()
    url = resolve_audio_url(key)
    if not url:
        raise HTTPException(status_code=404, detail=f"No audio found for '{key}'.")
    source = "local" if find_local_audio(key) else "wikimedia"
    return {"key": key, "url": url, "source": source}


# ─────────────────────────────────────────────────────────────────────────────
# COUNTRIES
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/countries")
def list_countries():
    return [
        {
            "name": name,
            "region": entry["region"],
            "instrument_count": len(entry["instruments"]),
            "has_audio": any(i["audio_key"] for i in entry["instruments"]),
        }
        for name, entry in sorted(DATA.items())
    ]


@app.get("/countries/{country}")
def get_country(country: str):
    match = next((k for k in DATA if k.lower() == country.lower()), None)
    if not match:
        raise HTTPException(status_code=404, detail=f"'{country}' bulunamadı.")
    entry = DATA[match]
    instruments_with_audio = []
    for inst in entry["instruments"]:
        audio_url = resolve_audio_url(inst["audio_key"]) if inst["audio_key"] else None
        instruments_with_audio.append({**inst, "audio_url": audio_url})
    return {"name": match, "region": entry["region"], "instruments": instruments_with_audio}


# ─────────────────────────────────────────────────────────────────────────────
# REGIONS
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/regions")
def list_regions():
    from collections import Counter
    counts = Counter(v["region"] for v in DATA.values())
    return [{"region": r, "country_count": c} for r, c in sorted(counts.items())]


@app.get("/regions/{region}")
def get_region(region: str):
    results = [
        {"name": name, "instrument_count": len(entry["instruments"])}
        for name, entry in sorted(DATA.items())
        if entry["region"].lower() == region.lower()
    ]
    if not results:
        raise HTTPException(status_code=404, detail=f"'{region}' bölgesi bulunamadı.")
    return {"region": region, "countries": results}


# ─────────────────────────────────────────────────────────────────────────────
# INSTRUMENTS
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/instruments")
def list_instruments(audio_only: bool = Query(False)):
    results = []
    for country, entry in sorted(DATA.items()):
        for inst in entry["instruments"]:
            if audio_only and not inst["audio_key"]:
                continue
            audio_url = resolve_audio_url(inst["audio_key"]) if inst["audio_key"] else None
            results.append({
                "country": country,
                "region": entry["region"],
                "name": inst["name"],
                "description": inst["description"],
                "emoji": inst["emoji"],
                "audio_key": inst["audio_key"],
                "audio_url": audio_url,
            })
    return results


@app.get("/instruments/search")
def search_instruments(q: str = Query(..., min_length=2)):
    q_lower = q.lower()
    results = []
    for country, entry in sorted(DATA.items()):
        for inst in entry["instruments"]:
            if q_lower in inst["name"].lower() or q_lower in inst["description"].lower():
                audio_url = resolve_audio_url(inst["audio_key"]) if inst["audio_key"] else None
                results.append({
                    "country": country,
                    "region": entry["region"],
                    "name": inst["name"],
                    "description": inst["description"],
                    "emoji": inst["emoji"],
                    "audio_url": audio_url,
                })
    if not results:
        raise HTTPException(status_code=404, detail=f"'{q}' için sonuç bulunamadı.")
    return {"query": q, "count": len(results), "results": results}
