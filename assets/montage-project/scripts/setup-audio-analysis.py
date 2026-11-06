"""Download official local audio-analysis weights after installing requirements-audio.txt.

Only public model downloads; no media uploads or account credentials required.
Run with .venv-audio/bin/python. Audio inference is provided by analyze-music.py.
"""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FOLDER = ROOT / ".models/audio"
os.environ.setdefault("HF_HOME", str(FOLDER / "hf-cache"))
os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["HF_HUB_DISABLE_XET"] = "1"


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main():
    from huggingface_hub import HfApi, snapshot_download
    import torch

    FOLDER.mkdir(parents=True, exist_ok=True)
    repo = "laion/clap-htsat-unfused"
    info = HfApi(token=False).model_info(repo)
    print(f"CLAP official revision {info.sha}", flush=True)
    snapshot_download(repo_id=repo, revision=info.sha, token=False,
                      local_dir=FOLDER / "clap", allow_patterns=["*.json", "*.txt", "pytorch_model.bin", "README.md"])
    separator = FOLDER / "hdemucs_high_trained.pt"
    url = "https://download.pytorch.org/torchaudio/models/hdemucs_high_trained.pt"
    if not separator.is_file():
        print("Downloading official TorchAudio HDemucs weights", flush=True)
        torch.hub.download_url_to_file(url, str(separator), progress=True)
    packages = {n: importlib.metadata.version(n) for n in ["torch", "torchaudio", "transformers", "librosa", "numpy", "scipy"]}
    manifest = {
        "checked": "2026-11-03", "packages": packages, "mediaUploaded": False,
        "models": [
            {"id": repo, "revision": info.sha, "source": "https://huggingface.co/" + repo,
             "license": "Apache-2.0", "folder": str(FOLDER / "clap"),
             "weightsSha256": digest(FOLDER / "clap/pytorch_model.bin")},
            {"id": "torchaudio/HDEMUCS_HIGH_MUSDB_PLUS", "source": url,
             "documentation": "https://docs.pytorch.org/audio/2.8.0/generated/torchaudio.pipelines.HDEMUCS_HIGH_MUSDB_PLUS.html",
             "license": "TorchAudio / original Demucs model provenance in official documentation",
             "file": str(separator), "weightsSha256": digest(separator)},
        ],
        "security": "Local inference; CLAP trust_remote_code=False and weights_only=True; separator plain state_dict weights_only=True.",
    }
    (FOLDER / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("Model downloads complete; .models/audio/manifest.json written", flush=True)


if __name__ == "__main__":
    main()
