"""
extract_note.py — Extract a clean single note from any instrument recording
============================================================================
Takes a messy recording (performance, demo, long sample) and extracts
the single cleanest note hit from it, exports a normalized WAV.

Usage:
    python extract_note.py input.mp3 output.wav
    python extract_note.py input.mp3 output.wav --duration 2.0 --onset 3
    python extract_note.py audio/tabla.mp3 audio/tabla_clean.wav --all

Requirements:
    pip install librosa soundfile numpy scipy
"""

import argparse
import numpy as np
import librosa
import soundfile as sf
from pathlib import Path


def extract_note(
    input_path: str,
    output_path: str,
    duration: float = 0.5,       # seconds to capture after onset
    onset_index: int = 0,        # which onset to use (0 = first, -1 = loudest)
    fade_out_ms: int = 100,      # fade out duration in ms to avoid clicks
    normalize: bool = True,      # normalize output to -3dBFS
    sr_target: int = 44100,      # output sample rate
) -> dict:
    """
    Extract a clean single note from a recording.
    Returns info dict with onset times and which one was selected.
    """
    print(f"  Loading: {input_path}")
    y, sr = librosa.load(input_path, sr=sr_target, mono=True)

    # ── Onset detection ────────────────────────────────────────────────────
    # Use both energy and spectral flux for robust onset detection
    onset_frames = librosa.onset.onset_detect(
        y=y,
        sr=sr,
        units="samples",
        hop_length=512,
        backtrack=True,          # snap to nearest energy trough before onset
        pre_max=20,
        post_max=20,
        pre_avg=100,
        post_avg=100,
        delta=0.07,
        wait=10,
    )

    if len(onset_frames) == 0:
        # No onsets detected — just take the start
        print("  ⚠  No onsets detected, using start of file")
        onset_frames = np.array([0])

    onset_times = librosa.samples_to_time(onset_frames, sr=sr)
    print(f"  Found {len(onset_frames)} onsets at: {[f'{t:.2f}s' for t in onset_times]}")

    # ── Select which onset to use ───────────────────────────────────────────
    if onset_index == -1:
        # Find the loudest onset (best for instruments with a clear attack)
        rms_values = []
        capture_samples = int(0.5 * sr)  # look at first 0.5s after each onset
        for onset_sample in onset_frames:
            end = min(onset_sample + capture_samples, len(y))
            segment = y[onset_sample:end]
            rms = np.sqrt(np.mean(segment ** 2))
            rms_values.append(rms)
        selected_idx = int(np.argmax(rms_values))
    else:
        selected_idx = min(onset_index, len(onset_frames) - 1)

    selected_onset = onset_frames[selected_idx]
    selected_time = onset_times[selected_idx]
    print(f"  Selected onset #{selected_idx} at {selected_time:.2f}s")

    # ── Extract segment ─────────────────────────────────────────────────────
    capture_samples = int(duration * sr)
    end_sample = min(selected_onset + capture_samples, len(y))
    note = y[selected_onset:end_sample]

    # ── Fade out to avoid clicks ────────────────────────────────────────────
    fade_samples = int((fade_out_ms / 1000) * sr)
    fade_samples = min(fade_samples, len(note))
    fade_curve = np.linspace(1.0, 0.0, fade_samples)
    note[-fade_samples:] *= fade_curve

    # ── Normalize ───────────────────────────────────────────────────────────
    if normalize:
        target_db = -3.0
        target_linear = 10 ** (target_db / 20)
        peak = np.max(np.abs(note))
        if peak > 0:
            note = note * (target_linear / peak)

    # ── Export ──────────────────────────────────────────────────────────────
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    sf.write(output_path, note, sr, subtype="PCM_16")
    print(f"  ✓ Saved {duration:.1f}s note → {output_path}")

    return {
        "input": input_path,
        "output": output_path,
        "all_onsets": onset_times.tolist(),
        "selected_onset_time": float(selected_time),
        "selected_onset_index": selected_idx,
        "output_duration": len(note) / sr,
    }


def batch_process_audio_folder(
    audio_dir: str = "audio",
    output_dir: str = "audio_clean",
    duration: float = 2.0,
    onset_index: int = -1,   # -1 = loudest onset
):
    """
    Process every file in audio/ folder and extract a clean note from each.
    Useful for cleaning up your entire Freesound download batch.
    """
    audio_path = Path(audio_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    extensions = {".mp3", ".ogg", ".wav", ".m4a", ".flac"}
    files = [f for f in audio_path.iterdir() if f.suffix.lower() in extensions]

    if not files:
        print(f"No audio files found in {audio_dir}/")
        return

    print(f"Processing {len(files)} files from {audio_dir}/ → {output_dir}/\n")
    results = []

    for f in sorted(files):
        out = output_path / f"{f.stem}.wav"
        print(f"[{f.name}]")
        try:
            info = extract_note(str(f), str(out), duration=duration, onset_index=onset_index)
            results.append({"status": "ok", **info})
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            results.append({"status": "error", "input": str(f), "error": str(e)})
        print()

    ok = sum(1 for r in results if r["status"] == "ok")
    print(f"Done: {ok}/{len(files)} files processed successfully.")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract a clean single note from an instrument recording")
    parser.add_argument("input",  nargs="?", help="Input audio file")
    parser.add_argument("output", nargs="?", help="Output WAV file")
    parser.add_argument("--duration",   type=float, default=2.0,  help="Capture duration in seconds (default: 2.0)")
    parser.add_argument("--onset",      type=int,   default=-1,   help="Which onset to use: 0=first, -1=loudest (default: -1)")
    parser.add_argument("--fade-out",   type=int,   default=100,  help="Fade-out duration in ms (default: 100)")
    parser.add_argument("--all",        action="store_true",      help="Batch process entire audio/ folder → audio_clean/")
    parser.add_argument("--audio-dir",  default="audio",          help="Input folder for --all mode (default: audio)")
    parser.add_argument("--output-dir", default="audio_clean",    help="Output folder for --all mode (default: audio_clean)")
    args = parser.parse_args()

    if args.all:
        batch_process_audio_folder(
            audio_dir=args.audio_dir,
            output_dir=args.output_dir,
            duration=args.duration,
            onset_index=args.onset,
        )
    elif args.input and args.output:
        extract_note(
            input_path=args.input,
            output_path=args.output,
            duration=args.duration,
            onset_index=args.onset,
            fade_out_ms=args.fade_out,
        )
    else:
        parser.print_help()
        print("\nExamples:")
        print("  python extract_note.py audio/tabla.mp3 audio/tabla_clean.wav")
        print("  python extract_note.py audio/oud.mp3 audio/oud_clean.wav --onset 0 --duration 3.0")
        print("  python extract_note.py --all                          # process entire audio/ folder")
        print("  python extract_note.py --all --output-dir audio_clean --duration 1.5")
