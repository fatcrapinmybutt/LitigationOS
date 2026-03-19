#!/usr/bin/env python
from __future__ import annotations
import argparse
from pathlib import Path
from huggingface_hub import snapshot_download

MODELS = {
    "phi3": ("microsoft/Phi-3-mini-4k-instruct", "Phi-3-mini-4k-instruct"),
    "tinyllama": ("TinyLlama/TinyLlama-1.1B-Chat-v1.0", "TinyLlama-1.1B-Chat-v1.0"),
    "minilm": ("sentence-transformers/all-MiniLM-L6-v2", "all-MiniLM-L6-v2"),
    "bge": ("BAAI/bge-small-en-v1.5", "bge-small-en-v1.5"),
    "e5": ("intfloat/e5-small-v2", "e5-small-v2"),
}

def dl(repo_id: str, out: Path):
    snapshot_download(
        repo_id=repo_id,
        local_dir=str(out),
        local_dir_use_symlinks=False,
    )

def main():
    ap = argparse.ArgumentParser(description="Download optional Hugging Face models for OrganizerStack.")
    ap.add_argument("--out", default=r"F:\LitigationOS\MODELS")
    ap.add_argument("--all", action="store_true")
    for k in MODELS:
        ap.add_argument(f"--{k}", action="store_true")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    selected = []
    if args.all:
        selected = list(MODELS.keys())
    else:
        for k in MODELS:
            if getattr(args, k):
                selected.append(k)

    if not selected:
        # sane default: small LLM + small embeddings
        selected = ["phi3", "minilm"]

    for k in selected:
        repo_id, folder = MODELS[k]
        dest = out / folder
        dest.mkdir(parents=True, exist_ok=True)
        print(f"Downloading {repo_id} -> {dest}")
        dl(repo_id, dest)

    print("Done.")

if __name__ == "__main__":
    main()
