"""Offline model-assisted music analysis for local videos/audio.

Run with .venv-audio/bin/python. CLAP compares real audio with candidate text
descriptions; its cosine scores are not calibrated probabilities. Optional
Hybrid Demucs estimates accompaniment and does not produce a guaranteed clean
music stem. Models must already be downloaded. No uploads or network requests.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
FFMPEG = ROOT / ".tools/runtime/bin/ffmpeg"
FFPROBE = ROOT / ".tools/runtime/bin/ffprobe"
DEFAULT_MODEL = "laion/clap-htsat-unfused"
SOURCES = ["drums", "bass", "other", "vocals"]

# English descriptions match CLAP's text training. Russian labels are for the
# report, and do not imply that a classifier ranking establishes ground truth.
CANDIDATES = {
    "presence": [
        ("speech_music", "Речь с фоновой музыкой", "A recording of a person speaking over background instrumental music."),
        ("speech_only", "Речь без музыки", "A recording of only a person speaking, with no music."),
        ("music_only", "Инструментальная музыка", "A recording of instrumental music playing, without speech."),
        ("effects", "Речь и звуковые эффекты", "A recording of speech with short sound effects and clicks, without background music."),
        ("noise", "Шум или артефакты", "A recording of distorted noise and audio processing artifacts."),
        ("silence", "Почти тишина", "A recording of near silence with faint background noise."),
    ],
    "style": [
        ("ambient_electronic", "Атмосферная электроника", "A recording of calm ambient electronic instrumental music with soft synthesizer pads."),
        ("rhythmic_electronic", "Ритмичная электроника", "A recording of rhythmic electronic instrumental background music with a steady beat and synthesizers."),
        ("lofi_hiphop", "Lo-fi / хип-хоп", "A recording of mellow lo-fi hip hop instrumental music with a relaxed drum beat."),
        ("orchestral", "Оркестровая / кинематографичная", "A recording of cinematic orchestral instrumental music with strings."),
        ("piano", "Фортепианная", "A recording of gentle piano instrumental background music."),
        ("guitar", "Гитарная", "A recording of acoustic guitar instrumental background music."),
        ("dance", "Танцевальная электронная", "A recording of upbeat electronic dance music with a driving four on the floor beat."),
        ("suspense_drone", "Напряжённый дрон", "A recording of dark suspenseful drone music with low sustained tones."),
        ("speech_residue", "Остатки речи после разделения", "A recording of muffled distorted human speech and vocal processing artifacts, not music."),
        ("noise", "Шум / артефакты", "A recording of noise, hiss, clicks and audio separation artifacts, not music."),
        ("silence", "Почти тишина", "A recording of almost silence and very faint background noise."),
    ],
    "mood": [
        ("calm", "Спокойная", "A recording of calm relaxed soft instrumental music."),
        ("upbeat", "Бодрая / позитивная", "A recording of upbeat cheerful optimistic instrumental music."),
        ("tense", "Напряжённая", "A recording of tense suspenseful dramatic instrumental music."),
        ("neutral", "Нейтральная фоновая", "A recording of unobtrusive neutral background instrumental music."),
        ("melancholic", "Меланхоличная", "A recording of sad melancholic instrumental music."),
        ("energetic", "Энергичная", "A recording of energetic intense instrumental music with strong percussion."),
        ("not_music", "Речь, шум или артефакты", "A recording of speech and noise rather than music."),
    ],
    "instruments": [
        ("synth_pads", "Синтезаторные подложки", "A recording of music with sustained synthesizer pads and electronic tones."),
        ("electronic_drums", "Электронные ударные", "A recording of music with electronic drum machine beats, kick drum and hi hats."),
        ("piano", "Фортепиано", "A recording of music featuring a piano playing notes and chords."),
        ("acoustic_guitar", "Акустическая гитара", "A recording of music featuring an acoustic guitar being plucked or strummed."),
        ("electric_guitar", "Электрогитара", "A recording of music featuring an electric guitar."),
        ("strings", "Струнные", "A recording of orchestral string instruments playing music."),
        ("bass", "Бас", "A recording of music with a prominent bass line and low bass notes."),
        ("acoustic_drums", "Акустические ударные", "A recording of music featuring an acoustic drum kit."),
        ("vocal_residue", "Остатки голоса", "A recording of distorted human voice, not musical instruments."),
        ("noise", "Шум / артефакты", "A recording of hiss and processing artifacts with no identifiable musical instruments."),
    ],
}


def run(command, **kwargs):
    return subprocess.run([str(x) for x in command], check=True, **kwargs)


def rms_db(audio):
    value = float(np.sqrt(np.mean(np.square(audio.astype(np.float64)))))
    return 20 * math.log10(max(value, 1e-12))


def peak_db(audio):
    return 20 * math.log10(max(float(np.max(np.abs(audio))), 1e-12))


def decode(path, start, seconds, sample_rate):
    result = run([
        FFMPEG, "-v", "error", "-ss", start, "-i", path, "-t", seconds,
        "-vn", "-ac", "2", "-ar", sample_rate, "-f", "f32le", "-",
    ], capture_output=True)
    audio = np.frombuffer(result.stdout, dtype="<f4").reshape(-1, 2).T.copy()
    if audio.shape[1] == 0:
        raise ValueError(f"No audio decoded from {path} at {start}s")
    return audio


def save_wav(path, audio, sample_rate):
    # Float WAV retains the estimated source levels; no loudness normalization.
    run([
        FFMPEG, "-n", "-v", "error", "-f", "f32le", "-ar", sample_rate,
        "-ac", audio.shape[0], "-i", "-", "-c:a", "pcm_f32le", path,
    ], input=np.asarray(audio.T, dtype="<f4").tobytes(), capture_output=True)


class Analyzer:
    def __init__(self, args):
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
        import torch
        from transformers import ClapModel, ClapProcessor

        self.torch = torch
        torch.set_num_threads(args.threads)
        torch.manual_seed(0)
        np.random.seed(0)
        self.device = args.device
        local_model = args.model_path or args.model_cache / "clap"
        model_name = str(local_model) if local_model.is_dir() else DEFAULT_MODEL
        kwargs = {"cache_dir": str(args.model_cache), "local_files_only": True,
                  "trust_remote_code": False}
        if args.revision:
            kwargs["revision"] = args.revision
        self.processor = ClapProcessor.from_pretrained(model_name, **kwargs)
        self.model = ClapModel.from_pretrained(model_name, weights_only=True, **kwargs).to(self.device).eval()
        descriptions = [row[2] for rows in CANDIDATES.values() for row in rows]
        tokens = self.processor(text=descriptions, padding=True, return_tensors="pt")
        with torch.inference_mode():
            embedding = self.model.get_text_features(**{k: v.to(self.device) for k, v in tokens.items()})
        self.text_embedding = torch.nn.functional.normalize(embedding, dim=-1)
        self.separator = None
        self.separator_path = None
        if args.separate:
            from torchaudio.models import hdemucs_high

            weight_path = args.separator_weights or args.model_cache / "hdemucs_high_trained.pt"
            if not weight_path.is_file():
                raise FileNotFoundError(f"Download official HDemucs weights first, then pass --separator-weights: {weight_path}")
            self.separator = hdemucs_high(sources=SOURCES).to(self.device).eval()
            state = torch.load(weight_path, map_location="cpu", weights_only=True)
            self.separator.load_state_dict(state)
            self.separator_path = str(weight_path.resolve())
        provenance_path = args.model_cache / "manifest.json"
        provenance = json.loads(provenance_path.read_text()) if provenance_path.is_file() else None
        recorded_revision = next((m.get("revision") for m in (provenance or {}).get("models", [])
                                  if m.get("id") == DEFAULT_MODEL), None)
        self.metadata = {
            "model": DEFAULT_MODEL, "modelPath": model_name,
            "revision": args.revision or recorded_revision or getattr(self.model.config, "_commit_hash", None),
            "provenanceManifest": str(provenance_path.resolve()) if provenance else None,
            "provenance": provenance,
            "localFilesOnly": True, "trustRemoteCode": False, "weightsOnly": True,
            "device": self.device,
            "versions": {p: importlib.metadata.version(p) for p in ["torch", "transformers", "numpy"]},
            "separator": "torchaudio HDEMUCS_HIGH_MUSDB_PLUS" if args.separate else None,
            "separatorWeights": self.separator_path,
            "scoreType": "cosine similarity; relative rankings among supplied descriptions, not calibrated probabilities",
        }

    def classify(self, audio, sample_rate, groups):
        import torch
        from torchaudio.functional import resample

        mono = self.torch.from_numpy(audio.mean(axis=0).copy())
        if sample_rate != 48000:
            mono = resample(mono, sample_rate, 48000)
        original_rms = rms_db(mono.numpy())
        gain_db = min(30.0, max(0.0, -20.0 - original_rms))
        mono = mono * (10 ** (gain_db / 20))
        # Explicit windows are <=10s; no random truncation of a whole video.
        inputs = self.processor(audio=mono.numpy(), sampling_rate=48000, return_tensors="pt")
        with torch.inference_mode():
            embedding = self.model.get_audio_features(**{k: v.to(self.device) for k, v in inputs.items()})
            embedding = torch.nn.functional.normalize(embedding, dim=-1)
            similarity = (embedding @ self.text_embedding.T)[0].cpu().numpy()
        output = {}
        offset = 0
        for name, rows in CANDIDATES.items():
            values = [{"key": key, "labelRu": label, "description": text,
                       "cosineSimilarity": round(float(similarity[offset + i]), 6)}
                      for i, (key, label, text) in enumerate(rows)]
            offset += len(rows)
            if name not in groups:
                continue
            ordered = sorted(values, key=lambda x: x["cosineSimilarity"], reverse=True)
            margin = ordered[0]["cosineSimilarity"] - ordered[1]["cosineSimilarity"]
            output[name] = {
                "candidates": values, "top3": ordered[:3], "top2Margin": round(margin, 6),
                "uncertainty": "small top-two margin; ambiguous relative ranking" if margin < 0.02 else "relative ranking only; not calibrated certainty",
            }
        return {"analysisInputGainDb": round(gain_db, 3), "groups": output}

    def separate(self, audio):
        if self.separator is None:
            return None
        torch = self.torch
        original_length = audio.shape[1]
        # CPU inference on one bounded window keeps memory usage predictable.
        waveform = torch.from_numpy(audio.copy()).to(self.device)
        center = waveform.mean()
        scale = waveform.mean(dim=0).std().clamp(min=1e-6)
        normalized = (waveform - center) / scale
        with torch.inference_mode():
            sources = self.separator(normalized.unsqueeze(0))[0, :, :, :original_length] * scale
            # Keep the adjustment in inference_mode: the result is an inference
            # tensor and cannot be modified outside that context.
            sources[SOURCES.index("vocals")] += center
        return sources.cpu().numpy()


def inputs_from_args(args):
    entries = []
    if args.manifest:
        manifest = json.loads(args.manifest.read_text())
        rows = manifest.get("references", []) if isinstance(manifest, dict) else manifest
        entries.extend({"ref": r.get("ref", i + 1), "source": r.get("source", r.get("path"))}
                       for i, r in enumerate(rows))
    entries.extend({"ref": Path(p).stem, "source": str(p)} for p in args.media)
    if not entries:
        raise ValueError("Provide local media files or --manifest")
    return entries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("media", type=Path, nargs="*")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--model-cache", type=Path, default=ROOT / ".models/audio")
    parser.add_argument("--model-path", type=Path)
    parser.add_argument("--revision")
    parser.add_argument("--separate", action="store_true")
    parser.add_argument("--separator-weights", type=Path)
    parser.add_argument("--windows", type=int, choices=[1, 3], default=3)
    parser.add_argument("--device", choices=["cpu", "mps"], default="cpu")
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--silence-rms-db", type=float, default=-65.0)
    parser.add_argument("--silence-peak-db", type=float, default=-50.0)
    args = parser.parse_args()
    entries = inputs_from_args(args)
    args.out.mkdir(parents=True, exist_ok=True)
    if (args.out / "analysis.json").exists():
        raise FileExistsError(f"Choose a fresh output folder: {args.out}")
    analyzer = Analyzer(args)
    result = {
        "createdUtc": datetime.now(timezone.utc).isoformat(),
        "modelAssistedAudioAnalysis": True, "humanAudition": False,
        "songIdentificationPerformed": False, "externalUpload": False,
        "model": analyzer.metadata, "references": [],
        "limitations": [
            "CLAP ranks the supplied descriptions and cannot identify song titles.",
            "Similarity values are not calibrated probabilities or proof of a genre/instrument.",
            "Accompaniment is an estimated separation, may retain speech and lose music.",
            "Only the saved fixed windows were analyzed, not the complete files.",
        ],
    }
    for entry in entries:
        source = Path(entry["source"]).expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(source)
        duration = float(run([FFPROBE, "-v", "error", "-show_entries", "format=duration",
                              "-of", "default=nw=1:nk=1", source], capture_output=True, text=True).stdout)
        fractions = [0.45] if args.windows == 1 else [0.1, 0.45, 0.8]
        starts = sorted(set(round(min(max(duration * fraction - 5, 0), max(0, duration - 10)), 3)
                            for fraction in fractions))
        record = {"ref": entry["ref"], "source": str(source), "durationSeconds": duration,
                  "songTitle": None, "windows": []}
        slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", str(entry["ref"])).strip("-")
        if not slug:
            slug = "audio-" + hashlib.sha256(str(source).encode()).hexdigest()[:8]
        for index, start in enumerate(starts, 1):
            print(f"Reference {entry['ref']}, window {index}/{len(starts)} at {start}s", flush=True)
            audio = decode(source, start, min(10, duration - start), 44100)
            prefix = f"ref-{slug}-window-{index:02d}"
            mix_path = args.out / (prefix + "-mix.wav")
            save_wav(mix_path, audio, 44100)
            window = {
                "startSeconds": start, "durationSeconds": round(audio.shape[1] / 44100, 4),
                "mixFile": str(mix_path.resolve()),
                "mixRmsDbfs": round(rms_db(audio), 3),
                "mixPresence": analyzer.classify(audio, 44100, ["presence"]),
                "musicEstimate": None, "assignedGenre": None,
            }
            stems = analyzer.separate(audio)
            if stems is not None:
                music = stems[:3].sum(axis=0)
                music_path = args.out / (prefix + "-estimated-music.wav")
                save_wav(music_path, music, 44100)
                music_rms, music_peak = rms_db(music), peak_db(music)
                silent = music_rms < args.silence_rms_db or music_peak < args.silence_peak_db
                estimate = {
                    "file": str(music_path.resolve()), "cleanStem": False,
                    "rmsDbfs": round(music_rms, 3), "peakDbfs": round(music_peak, 3),
                    "stemRmsDbfs": {name: round(rms_db(stems[i]), 3) for i, name in enumerate(SOURCES)},
                    "nearSilent": silent, "classification": None,
                    "status": "too quiet for a genre assignment" if silent else "estimated accompaniment; relative model ranking only",
                }
                if not silent:
                    estimate["classification"] = analyzer.classify(music, 44100, list(CANDIDATES))
                window["musicEstimate"] = estimate
            else:
                window["mixedMusicCandidates"] = analyzer.classify(audio, 44100, ["style", "mood", "instruments"])
                window["status"] = "mixed speech/music; no clean music estimate; rankings may reflect speech"
            record["windows"].append(window)
            # Retain progress if interrupted, without marking analysis complete.
            (args.out / "progress.json").write_text(json.dumps({**result, "current": record}, ensure_ascii=False, indent=2) + "\n")
        result["references"].append(record)
    result["complete"] = True
    (args.out / "analysis.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(f"Saved model-assisted audio analysis: {args.out / 'analysis.json'}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Audio analysis failed: {exc}", file=sys.stderr)
        raise
