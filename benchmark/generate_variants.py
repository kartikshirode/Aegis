"""Deterministic adversarial variant generator for the Aegis detection benchmark.

Given N originals (CC-licensed sports clips), produce M variants per transform
category. The full corpus is reproducible from a fixed seed.

Transform categories (single-transform):
  reencode       - H.264 at 5 bitrates (200k, 400k, 800k, 1.5M, 3M)
  crop           - centered crops at 3 ratios (0.85, 0.70, 0.55 of each axis)
  mirror         - horizontal flip
  upscale        - 2x via ffmpeg lanczos (AI-upscale stand-in; swap for Real-ESRGAN in Phase 2)
  overlay        - caption / logo overlay in the top-left

Multi-transform chains (subset of originals):
  chain_2  - random ordered pair from the single-transform set
  chain_3  - random ordered triple

Usage:
  python benchmark/generate_variants.py \
      --originals data/originals \
      --out data/adversarial \
      --seed 2026 \
      --n-originals 30 \
      --chain-samples 50

Rerunning with the same seed reproduces the corpus byte-for-byte (modulo ffmpeg
version drift; the ffmpeg version is pinned in benchmark/README.md).
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import random
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable

SINGLE_TRANSFORMS = ("reencode", "crop", "mirror", "upscale", "overlay")
BITRATES_KBPS = (200, 400, 800, 1500, 3000)
CROP_RATIOS = (0.85, 0.70, 0.55)

# libx264 requires even width AND height. Float-multiplied filter expressions
# (iw/0.55, etc.) emit odd-by-one pixels due to binary representation of 0.55.
# Append this filter to every video filter chain as the last stage to snap.
EVEN_DIMS_FILTER = "scale=trunc(iw/2)*2:trunc(ih/2)*2"


def _drawtext_fontfile() -> str:
    """Return an ffmpeg-escaped font path for drawtext.

    ffmpeg's drawtext uses `:` as option delimiter, so Windows drive-letter
    colons must be escaped as `\\:`. On Windows: Arial. On *nix: DejaVuSans
    which is present on most distros.
    """
    if platform.system() == "Windows":
        p = "C:/Windows/Fonts/arial.ttf"
        return p.replace(":", r"\:")
    candidates = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
    )
    for c in candidates:
        if os.path.exists(c):
            return c
    return "DejaVuSans"  # best-effort fallback; ffmpeg errors loudly if missing


@dataclass
class VariantRecord:
    variant_id: str
    source: str
    transform_chain: list[str]
    params: dict
    path: str


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--originals", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--seed", type=int, default=2026)
    p.add_argument("--n-originals", type=int, default=30)
    p.add_argument("--chain-samples", type=int, default=50)
    args = p.parse_args()

    rng = random.Random(args.seed)

    sources = sorted(args.originals.glob("*.mp4"))
    if len(sources) < args.n_originals:
        raise SystemExit(
            f"need >={args.n_originals} .mp4 originals in {args.originals}, found {len(sources)}"
        )
    sources = sources[: args.n_originals]

    args.out.mkdir(parents=True, exist_ok=True)
    records: list[VariantRecord] = []

    # Single-transform variants (deterministic order)
    for src in sources:
        for kind in SINGLE_TRANSFORMS:
            records.extend(_emit_single(src, kind, args.out, rng))

    # Multi-transform chains
    for _ in range(args.chain_samples):
        src = rng.choice(sources)
        chain_len = rng.choice((2, 3))
        chain = rng.sample(SINGLE_TRANSFORMS, chain_len)
        records.append(_emit_chain(src, chain, args.out, rng))

    manifest = args.out / "manifest.json"
    manifest.write_text(json.dumps([asdict(r) for r in records], indent=2))
    print(f"wrote {len(records)} variants; manifest at {manifest}")


# ---------- single-transform emitters ----------

def _emit_single(src: Path, kind: str, out: Path, rng: random.Random) -> list[VariantRecord]:
    if kind == "reencode":
        return [_reencode(src, br, out) for br in BITRATES_KBPS]
    if kind == "crop":
        return [_crop(src, r, out) for r in CROP_RATIOS]
    if kind == "mirror":
        return [_mirror(src, out)]
    if kind == "upscale":
        return [_upscale(src, out)]
    if kind == "overlay":
        return [_overlay(src, out)]
    raise ValueError(kind)


def _with_even_dims(vf: str) -> str:
    """Guarantee libx264-compatible output dims by appending the snap-to-even filter."""
    return f"{vf},{EVEN_DIMS_FILTER}"


def _reencode(src: Path, kbps: int, out: Path) -> VariantRecord:
    dst = out / f"{src.stem}_reencode_{kbps}k.mp4"
    # Re-encode preserves input dims but some HMDB-51 clips are odd-height;
    # apply the safety filter unconditionally.
    _ffmpeg(["-i", str(src), "-vf", EVEN_DIMS_FILTER, "-b:v", f"{kbps}k", "-c:v", "libx264", "-preset", "veryfast", "-c:a", "aac", str(dst)])
    return VariantRecord(dst.stem, str(src), ["reencode"], {"kbps": kbps}, str(dst))


def _crop(src: Path, ratio: float, out: Path) -> VariantRecord:
    dst = out / f"{src.stem}_crop_{int(ratio*100)}.mp4"
    # centered crop to `ratio` on both axes, then scale back to original size
    vf = _with_even_dims(f"crop=iw*{ratio}:ih*{ratio}:iw*(1-{ratio})/2:ih*(1-{ratio})/2,scale=iw/{ratio}:ih/{ratio}")
    _ffmpeg(["-i", str(src), "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-c:a", "copy", str(dst)])
    return VariantRecord(dst.stem, str(src), ["crop"], {"ratio": ratio}, str(dst))


def _mirror(src: Path, out: Path) -> VariantRecord:
    dst = out / f"{src.stem}_mirror.mp4"
    _ffmpeg(["-i", str(src), "-vf", _with_even_dims("hflip"), "-c:v", "libx264", "-preset", "veryfast", "-c:a", "copy", str(dst)])
    return VariantRecord(dst.stem, str(src), ["mirror"], {}, str(dst))


def _upscale(src: Path, out: Path) -> VariantRecord:
    dst = out / f"{src.stem}_upscale2x.mp4"
    _ffmpeg(["-i", str(src), "-vf", _with_even_dims("scale=iw*2:ih*2:flags=lanczos"), "-c:v", "libx264", "-preset", "veryfast", "-c:a", "copy", str(dst)])
    return VariantRecord(dst.stem, str(src), ["upscale"], {"factor": 2}, str(dst))


def _overlay(src: Path, out: Path) -> VariantRecord:
    dst = out / f"{src.stem}_overlay.mp4"
    # white text on dark semitransparent box, top-left.
    # drawtext needs an explicit fontfile on Windows (no default font path).
    font = _drawtext_fontfile()
    vf = _with_even_dims(
        "drawbox=x=10:y=10:w=300:h=40:color=black@0.4:t=fill,"
        f"drawtext=fontfile='{font}':text='LIVE STREAM':x=25:y=20:fontsize=22:fontcolor=white"
    )
    _ffmpeg(["-i", str(src), "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-c:a", "copy", str(dst)])
    return VariantRecord(dst.stem, str(src), ["overlay"], {}, str(dst))


# ---------- chain emitter ----------

def _emit_chain(src: Path, chain: list[str], out: Path, rng: random.Random) -> VariantRecord:
    current = src
    params: dict = {}
    for step in chain:
        if step == "reencode":
            kbps = rng.choice(BITRATES_KBPS)
            current_record = _reencode(current, kbps, out)
            params.setdefault("reencode", {"kbps": kbps})
        elif step == "crop":
            ratio = rng.choice(CROP_RATIOS)
            current_record = _crop(current, ratio, out)
            params.setdefault("crop", {"ratio": ratio})
        elif step == "mirror":
            current_record = _mirror(current, out)
            params.setdefault("mirror", {})
        elif step == "upscale":
            current_record = _upscale(current, out)
            params.setdefault("upscale", {"factor": 2})
        elif step == "overlay":
            current_record = _overlay(current, out)
            params.setdefault("overlay", {})
        else:
            raise ValueError(step)
        current = Path(current_record.path)

    # Rename the final output to reflect the chain for clarity
    dst = out / f"{src.stem}_chain_{'_'.join(chain)}.mp4"
    current.rename(dst)
    return VariantRecord(dst.stem, str(src), chain, params, str(dst))


# ---------- ffmpeg glue ----------

def _ffmpeg(args: list[str]) -> None:
    subprocess.run(
        ["ffmpeg", "-nostdin", "-y", "-loglevel", "error", *args],
        check=True,
    )


if __name__ == "__main__":
    main()
