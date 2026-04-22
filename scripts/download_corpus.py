"""Download 30 CC-BY-4.0 sport clips from HMDB-51 for the Aegis benchmark + demo corpus.

Source: divm/hmdb51 on HuggingFace — a mirror of HMDB-51 that pre-extracts the
original .rar archive into per-clip .mp4 files, organised under test/ and train/
subdirectories and named by action class.

Upstream: HMDB-51, Kuehne, Jhuang, Garrote, Poggio, Serre, ICCV 2011
License: CC-BY-4.0 (per the Serre Lab site)

Target: 30 clips across 8 sport-plausible classes. Output:
    data/originals/match-NN.mp4          (30 files, clean-renamed)
    data/originals/LICENSES.md           (CC-BY-4.0 attribution per clip)
    data/originals/.benchmark_clip_map.json  (stem -> clip_id map, populated by benchmark/run.py on ingest)

Rerunning this script is safe — it skips files already present.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from huggingface_hub import HfApi, hf_hub_download

REPO_ID = "divm/hmdb51"
REPO_TYPE = "dataset"

# Pick only classes that are unambiguously sport-plausible. Avoids:
#  shoot_gun, shoot_bow — weapon optics, off-brand for sports media story
#  ride_horse — fine but low-resolution HMDB clips are visually weak
SPORT_CLASSES = [
    ("catch",              4),
    ("dribble",            4),
    ("golf",               4),
    ("kick_ball",          4),
    ("ride_bike",          4),
    ("shoot_ball",         4),
    ("swing_baseball",     3),  # class folder on HF is actually "swing_baseball" not "swing_baseball_bat"
    ("throw",              3),
]
TOTAL_TARGET = sum(n for _, n in SPORT_CLASSES)
assert TOTAL_TARGET == 30

OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "originals"
LICENSES_MD = OUT_DIR / "LICENSES.md"


@dataclass
class Pick:
    class_name: str
    repo_path: str        # e.g. "train/catch_.....mp4"
    local_name: str       # e.g. "match-01.mp4"


def list_candidates(api: HfApi, class_name: str) -> list[str]:
    """Return every file in the HF repo whose basename starts with `{class_name}_`."""
    all_files = api.list_repo_files(REPO_ID, repo_type=REPO_TYPE)
    return sorted(
        p for p in all_files
        if p.endswith(".mp4") and Path(p).name.lower().startswith(class_name.lower() + "_")
    )


def ffprobe_duration(path: Path) -> float | None:
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, check=True,
        )
        return float(r.stdout.strip())
    except Exception:
        return None


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    api = HfApi()
    picks: list[Pick] = []
    serial = 0

    for class_name, want in SPORT_CLASSES:
        candidates = list_candidates(api, class_name)
        if len(candidates) < want:
            print(f"[warn] class {class_name!r}: only {len(candidates)} available, wanted {want}", file=sys.stderr)
            want = len(candidates)
        for repo_path in candidates[:want]:
            serial += 1
            picks.append(Pick(
                class_name=class_name,
                repo_path=repo_path,
                local_name=f"match-{serial:02d}.mp4",
            ))

    print(f"[info] selected {len(picks)} clips across {len(SPORT_CLASSES)} sport classes")

    manifest: list[dict] = []
    for p in picks:
        local_path = OUT_DIR / p.local_name
        if local_path.exists() and local_path.stat().st_size > 0:
            print(f"[skip] {p.local_name} already present")
        else:
            print(f"[pull] {p.local_name}  <-  {p.repo_path}")
            try:
                cached = hf_hub_download(
                    repo_id=REPO_ID,
                    repo_type=REPO_TYPE,
                    filename=p.repo_path,
                    local_dir=str(OUT_DIR / "_cache"),
                )
                # Copy-rename to the clean local name. Not a move — keep cache so
                # rerunning the script is fast.
                local_path.write_bytes(Path(cached).read_bytes())
            except Exception as e:
                print(f"[err]  {p.local_name}: {e}", file=sys.stderr)
                continue

        duration = ffprobe_duration(local_path)
        manifest.append({
            "file":        p.local_name,
            "class":       p.class_name,
            "source_repo": f"{REPO_ID}:{p.repo_path}",
            "duration_s":  duration,
            "size_bytes":  local_path.stat().st_size,
        })

    # Write LICENSES.md
    _write_licenses(manifest)

    # Summary
    ok = sum(1 for m in manifest if m["size_bytes"] > 0)
    print(f"\n[done] {ok}/{len(picks)} clips in {OUT_DIR}")
    print(f"[done] license + attribution: {LICENSES_MD}")
    return 0 if ok == len(picks) else 1


def _write_licenses(manifest: list[dict]) -> None:
    lines = [
        "# Sport corpus — licenses, attribution, and redistribution boundary",
        "",
        "Every `.mp4` in this directory is a clip from **HMDB-51** (human-action",
        "recognition dataset, Serre Lab, Brown University, ICCV 2011).",
        "",
        "## Dataset-level license",
        "",
        "**License:** [Creative Commons Attribution 4.0 International (CC-BY-4.0)](https://creativecommons.org/licenses/by/4.0/)",
        "",
        "**Required attribution:**",
        "",
        "> Kuehne, H., Jhuang, H., Garrote, E., Poggio, T., Serre, T. ",
        "> *HMDB: a large video database for human motion recognition.* ",
        "> International Conference on Computer Vision (ICCV), 2011. ",
        "> <https://serre.lab.brown.edu/hmdb51.html>",
        "",
        "**Accessed via:** the `divm/hmdb51` HuggingFace mirror, which hosts per-clip",
        "pre-extracted `.mp4` files derived from the Serre Lab RAR archive.",
        "",
        "## Residual copyright — read before use",
        "",
        "HMDB-51 was compiled from **mixed source footage** — YouTube user uploads, DVDs,",
        "and broadcast clips (examples visible in the manifest below: 'Tour de France',",
        "'APOCALYPTO', 'BRIAN CLOUGH'). The Serre Lab's CC-BY-4.0 license applies to the",
        "**dataset as a research compilation** — the act of collecting, organising,",
        "labelling, and publishing the corpus. Individual clips may retain residual",
        "copyright from their original sources.",
        "",
        "This is HMDB-51's well-known posture and is how every downstream paper handles",
        "it. Aegis inherits the same discipline:",
        "",
        "1. **Benchmark use only.** These clips feed `backend/detect.py` in the LOCAL",
        "   pipeline and `benchmark/run.py` to compute recall / match-rate / precision.",
        "   They never leave the developer or Cloud Run environment.",
        "2. **Not redistributed.** `.gitignore` excludes `data/originals/*.mp4`. They are",
        "   not in the public GitHub repo, not in the benchmark results JSON, and not in",
        "   the submission tarball.",
        "3. **Not shown in the public demo video.** The 2:45 demo video published on",
        "   YouTube uses **team-generated** or **clearly-CC-licensed** footage for every",
        "   on-screen moment — see `docs/demo-cold-open.md` and `data/case-study/`. No",
        "   HMDB-51 clip is ever rendered to a public surface.",
        "4. **Derived artefacts (benchmark variants) inherit the same boundary.** The",
        "   output of `benchmark/generate_variants.py` is also gitignored and not",
        "   published in any submission artefact.",
        "",
        "If your reviewer needs a CC-0-clean corpus (no residual copyright anywhere), swap",
        "HMDB-51 for a Pexels / Pixabay / Mixkit custom download in `scripts/download_corpus.py`.",
        "The rest of the pipeline is indifferent to the source.",
        "",
        "## Clip manifest",
        "",
        "| File | Class | Source path (repo) | Duration (s) | Size (bytes) |",
        "|---|---|---|---:|---:|",
    ]
    for m in manifest:
        dur = f"{m['duration_s']:.2f}" if m.get("duration_s") else "?"
        lines.append(f"| {m['file']} | {m['class']} | {m['source_repo']} | {dur} | {m['size_bytes']:,} |")

    lines.extend([
        "",
        "## Notes",
        "",
        "- Rerunning `scripts/download_corpus.py` is idempotent — it skips files already present.",
        "- The `_cache/` subdirectory holds the HuggingFace snapshot download (gitignored).",
        "- `.benchmark_clip_map.json` is written by `benchmark/run.py --ingest-first` and maps",
        "  source stems to clip UUIDs issued at ingest time.",
    ])

    LICENSES_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
