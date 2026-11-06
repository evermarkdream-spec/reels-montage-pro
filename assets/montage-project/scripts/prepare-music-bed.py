#!/usr/bin/env python3
"""Prepare a separate, voice-ducked music WAV for Remotion (volume=1).

Uses FFmpeg/FFprobe only. Inputs remain unchanged. The initial loudness gap is
an adjustable starting point, not a guarantee of a subjectively good blend.
Auditory review remains necessary and is never claimed by this script.

Example:
  .venv/bin/python scripts/prepare-music-bed.py --music track.wav \
    --voice voice-edited.wav --voice-gain-db 9 --gap-db 18 \
    --out out/music/prepared.wav --preview-out out/music/preview.wav

The output contains MUSIC ONLY, already attenuated and ducked by the actual
post-gain voice. Use this WAV in a separate Remotion Audio node at volume=1;
keep the voice node and its existing gain separate. --preview-out optionally
creates a reference mix for measurement/listening; do not also add it to the
composition, or the voice will be doubled.
"""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]


def binary(name):
    bundled = ROOT / ".tools" / "runtime" / "bin" / name
    found = str(bundled) if bundled.is_file() else shutil.which(name)
    if not found:
        raise ValueError(f"{name} not found in bundled runtime or PATH")
    return found


def run(command):
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        raise ValueError(result.stderr[-6000:].strip() or "FFmpeg command failed")
    return result


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def probe(ffprobe, path):
    data = json.loads(run([
        ffprobe, "-v", "error", "-select_streams", "a:0",
        "-show_entries", "stream=codec_name,duration,channels,sample_rate:format=duration",
        "-of", "json", str(path),
    ]).stdout)
    if not data.get("streams"):
        raise ValueError(f"No audio stream: {path}")
    stream = data["streams"][0]
    duration = stream.get("duration") or data.get("format", {}).get("duration")
    try:
        duration = float(duration)
    except (ValueError, TypeError):
        raise ValueError(f"Cannot determine duration: {path}")
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError(f"Invalid audio duration: {path}")
    return {**stream, "durationSeconds": duration}


def measure(ffmpeg, path, duration, gain_db=0, loop=False):
    command = [ffmpeg, "-nostdin", "-hide_banner", "-nostats"]
    if loop:
        command += ["-stream_loop", "-1"]
    command += [
        "-i", str(path), "-vn", "-af",
        f"volume={gain_db:.8f}dB,apad,atrim=duration={duration:.8f},ebur128=peak=true",
        "-f", "null", "-",
    ]
    log = run(command).stderr
    summary = log[log.rfind("Summary:"):]
    integrated = re.search(r"Integrated loudness:\s*I:\s*([-+\w.]+)\s*LUFS", summary)
    peak = re.search(r"True peak:\s*Peak:\s*([-+\w.]+)\s*dBFS", summary)
    lra = re.search(r"Loudness range:\s*LRA:\s*([-+\w.]+)\s*LU", summary)
    if not integrated or not peak:
        raise ValueError("Cannot parse FFmpeg EBU R128 summary:\n" + summary)
    values = {"integratedLufs": float(integrated[1]), "truePeakDbfs": float(peak[1])}
    if lra:
        values["loudnessRangeLu"] = float(lra[1])
    if not all(math.isfinite(value) for value in values.values()):
        raise ValueError(f"Audio is silent or unmeasurable: {path}")
    return values


def install_file(temporary, destination, overwrite):
    if overwrite:
        os.replace(temporary, destination)
    else:
        # O_EXCL protects against a destination appearing after the initial check.
        with temporary.open("rb") as source, destination.open("xb") as target:
            shutil.copyfileobj(source, target)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--music", type=Path, required=True)
    parser.add_argument("--voice", type=Path, required=True)
    parser.add_argument("--voice-gain-db", type=float, default=0)
    parser.add_argument("--duration", type=float, help="Seconds; defaults to voice duration")
    parser.add_argument("--out", type=Path, required=True, help="Prepared music-only WAV")
    parser.add_argument("--preview-out", type=Path, help="Optional voice+music reference WAV")
    parser.add_argument("--gap-db", type=float, default=18, help="Initial base music LUFS below post-gain voice (default 18)")
    parser.add_argument("--fade-in", type=float, default=0.6)
    parser.add_argument("--fade-out", type=float, default=1.2)
    parser.add_argument("--duck-threshold-db", type=float, help="Sidechain RMS threshold; defaults to voice LUFS minus 6, clamped to -60..-12 dB")
    parser.add_argument("--duck-ratio", type=float, default=3)
    parser.add_argument("--duck-attack-ms", type=float, default=20)
    parser.add_argument("--duck-release-ms", type=float, default=350)
    parser.add_argument("--loop", action="store_true", help="Explicitly permit repeating a short source; loop seams require listening")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    music, voice, output = [p.expanduser().resolve() for p in (args.music, args.voice, args.out)]
    preview = args.preview_out.expanduser().resolve() if args.preview_out else None
    report_path = output.with_suffix(".json")
    targets = [output, report_path] + ([preview] if preview else [])
    if len(set(targets)) != len(targets):
        raise ValueError("Music, preview and report destinations must be distinct")
    if any(target in (music, voice) for target in targets):
        raise ValueError("Output must not replace a source, even with --overwrite")
    if any(target.suffix.lower() != ".wav" for target in [output] + ([preview] if preview else [])):
        raise ValueError("Music and preview outputs must be WAV files")
    for source in (music, voice):
        if not source.is_file():
            raise ValueError(f"Input not found: {source}")
    for target in targets:
        if target.exists() and not args.overwrite:
            raise ValueError(f"Output exists; use --overwrite explicitly: {target}")
    numbers = [args.voice_gain_db, args.gap_db, args.fade_in, args.fade_out,
               args.duck_ratio, args.duck_attack_ms, args.duck_release_ms]
    if not all(math.isfinite(value) for value in numbers):
        raise ValueError("Numeric parameters must be finite")
    if not 0 <= args.gap_db <= 60 or not -60 <= args.voice_gain_db <= 30:
        raise ValueError("Use gap 0..60 dB and voice gain -60..30 dB")
    if min(args.fade_in, args.fade_out) < 0:
        raise ValueError("Fade durations cannot be negative")
    if not 1 <= args.duck_ratio <= 20 or not 0.01 <= args.duck_attack_ms <= 2000 or not 0.01 <= args.duck_release_ms <= 9000:
        raise ValueError("Ducking parameters outside FFmpeg limits")

    ffmpeg, ffprobe = binary("ffmpeg"), binary("ffprobe")
    music_info, voice_info = probe(ffprobe, music), probe(ffprobe, voice)
    duration = args.duration if args.duration is not None else voice_info["durationSeconds"]
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("Duration must be positive and finite")
    if music_info["durationSeconds"] + 0.02 < duration and not args.loop:
        raise ValueError(f"Music is too short ({music_info['durationSeconds']:.3f}s < {duration:.3f}s). Choose a longer track or explicitly pass --loop")

    voice_levels = measure(ffmpeg, voice, duration, args.voice_gain_db)
    music_levels = measure(ffmpeg, music, duration, loop=args.loop)
    target_music_lufs = voice_levels["integratedLufs"] - args.gap_db
    music_gain_db = target_music_lufs - music_levels["integratedLufs"]
    # A large positive gain suggests a bad source/measurement; never amplify blindly.
    if music_gain_db > 30:
        raise ValueError("Music would require over +30 dB gain; inspect source first")
    threshold_db = args.duck_threshold_db
    if threshold_db is None:
        threshold_db = max(-60, min(-12, voice_levels["integratedLufs"] - 6))
    if not math.isfinite(threshold_db) or not -60 <= threshold_db <= 0:
        raise ValueError("Ducking threshold must be -60..0 dB")
    threshold = max(0.000976563, 10 ** (threshold_db / 20))
    fade_in, fade_out = min(args.fade_in, duration / 3), min(args.fade_out, duration / 3)
    fmt = "aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo"
    bed_filters = f"{fmt},volume={music_gain_db:.8f}dB,apad,atrim=duration={duration:.8f},asetpts=PTS-STARTPTS"
    if fade_in:
        bed_filters += f",afade=t=in:d={fade_in:.8f}"
    if fade_out:
        bed_filters += f",afade=t=out:st={duration-fade_out:.8f}:d={fade_out:.8f}"
    filters = (
        f"[0:a:0]{bed_filters}[bed];"
        f"[1:a:0]{fmt},volume={args.voice_gain_db:.8f}dB,apad,atrim=duration={duration:.8f},asetpts=PTS-STARTPTS[control];"
        f"[bed][control]sidechaincompress=threshold={threshold:.9f}:ratio={args.duck_ratio:.8f}:"
        f"attack={args.duck_attack_ms:.8f}:release={args.duck_release_ms:.8f}:makeup=1:detection=rms,"
        f"apad,atrim=duration={duration:.8f}[prepared]"
    )
    for target in targets:
        target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".prepare-music-", dir=output.parent) as temporary:
        temporary = Path(temporary)
        prepared = temporary / "prepared.wav"
        cmd = [ffmpeg, "-nostdin", "-hide_banner", "-v", "error"]
        if args.loop:
            cmd += ["-stream_loop", "-1"]
        cmd += ["-i", str(music), "-i", str(voice), "-filter_complex", filters,
                "-map", "[prepared]", "-c:a", "pcm_s24le", "-ar", "48000", str(prepared)]
        run(cmd)
        prepared_levels = measure(ffmpeg, prepared, duration)
        preview_levels = None
        temporary_preview = temporary / "preview.wav"
        if preview:
            mix = (f"[0:a:0]{fmt},volume={args.voice_gain_db:.8f}dB,apad,atrim=duration={duration:.8f}[v];"
                   f"[v][1:a:0]amix=inputs=2:normalize=0:duration=longest,atrim=duration={duration:.8f}[mix]")
            run([ffmpeg, "-nostdin", "-hide_banner", "-v", "error", "-i", str(voice), "-i", str(prepared),
                 "-filter_complex", mix, "-map", "[mix]", "-c:a", "pcm_s24le", "-ar", "48000", str(temporary_preview)])
            preview_levels = measure(ffmpeg, temporary_preview, duration)
        report = {
            "musicSource": {"path": str(music), "sha256": sha256(music), "probe": music_info, "levelsBeforeGain": music_levels},
            "voiceSource": {"path": str(voice), "sha256": sha256(voice), "probe": voice_info, "gainDb": args.voice_gain_db, "postGainLevels": voice_levels},
            "durationSeconds": duration,
            "initialGapDb": args.gap_db,
            "initialTargetMusicLufs": target_music_lufs,
            "musicGainDb": music_gain_db,
            "ducking": {"thresholdDb": threshold_db, "ratio": args.duck_ratio, "attackMs": args.duck_attack_ms, "releaseMs": args.duck_release_ms, "control": "actual post-gain voice"},
            "fadeInSeconds": fade_in, "fadeOutSeconds": fade_out,
            "explicitLoop": args.loop,
            "preparedMusic": {"path": str(output), "levels": prepared_levels, "sha256": sha256(prepared), "remotionVolume": 1, "containsNarration": False,
                              "achievedGapBelowVoiceLu": voice_levels["integratedLufs"] - prepared_levels["integratedLufs"]},
            "previewMix": {"path": str(preview), "levels": preview_levels, "clippingRisk": preview_levels["truePeakDbfs"] >= 0} if preview else None,
            "auditoryReview": False,
            "notes": ["Initial levels and ducking need auditory review; not a guaranteed subjective blend.",
                      "Prepared WAV contains music only. Keep the original voice node and gain separate.",
                      "Preview contains voice+music; do not add it alongside the voice node.",
                      "Explicit looping repeats the source; inspect loop seams by ear." if args.loop else "No source looping was requested."],
            "filterGraph": filters,
        }
        temporary_report = temporary / "report.json"
        temporary_report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        install_file(prepared, output, args.overwrite)
        if preview:
            install_file(temporary_preview, preview, args.overwrite)
        install_file(temporary_report, report_path, args.overwrite)
    print(json.dumps({"music": str(output), "report": str(report_path), "preview": str(preview) if preview else None,
                      "musicLufs": prepared_levels["integratedLufs"], "previewLevels": preview_levels,
                      "auditoryReview": False}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
