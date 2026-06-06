@echo off
echo 🎵 World Instruments Explorer
echo ==============================

echo 📦 Installing dependencies...
pip install -r requirements.txt

echo.
echo ✅ Starting API server at http://localhost:8000
echo 📖 Swagger docs at  http://localhost:8000/docs
echo 🌍 Open index.html in your browser to use the app
echo.
echo Press Ctrl+C to stop.
echo.

uvicorn main:app --reload --host 0.0.0.0 --port 8000
