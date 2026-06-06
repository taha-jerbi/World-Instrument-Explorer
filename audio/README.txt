DROP YOUR AUDIO FILES HERE
==========================

Supported formats: .mp3  .ogg  .wav  .m4a  .flac

Naming convention:
  The filename (without extension) must match the instrument's audio key.
  The key is the instrument name in lowercase with spaces replaced by underscores.

Examples:
  tabla.mp3
  oud.ogg
  steel_pan.mp3
  hardanger_fiddle.wav
  uilleann_pipes.ogg

How it works:
  1. Drop your file in this folder (e.g.  tabla.mp3)
  2. Make sure uvicorn is running  (start.bat / start.sh)
  3. Click ▶ in the browser — the backend streams it directly, no CORS issues

Priority:
  Local files in this folder always take priority over Wikimedia URLs.
  If no local file exists, the backend falls back to the Wikimedia URL in models.py.
  If neither exists, the frontend plays a synthesized sound.
