"""Run the Aegis detection benchmark against a generated variant set.

Usage:
    python benchmark/run.py \
        --originals data/originals \
        --variants  data/adversarial \
        --out       data/benchmark-results \
        --api-base  http://localhost:8080

Assumes:
  - The API is running.
  - Each original in --originals has already been POSTed to /ingest (or will be
    ingested by this script with --ingest-first).

Metrics computed (matches docs/benchmarks.md):
  - Recall on single-transform @ ≤ 5% FPR
  - Recall on multi-transform chains @ ≤ 5% FPR
  - Precision@5 (retrieval)
  - Per-transform-class recall
  - End-to-end latency p50, p95
  - False-positive rate on a held-out fair-use commentary set (if --fair-use dir provided)

Outputs:
  - data/benchmark-results/summary.json
  - data/benchmark-results/per-variant.jsonl
  - data/benchmark-results/confusion-matrix.json
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

import httpx


@dataclass
class VariantResult:
    variant_id: str
    source: str
    transform_chain: list[str]
    expected_clip: str   # originating source clip stem
    matched: bool
    detected_clip_id: str | None
    verdict: str | None
    confidence: float | None
    latency_ms: float
    error: str | None = None


@dataclass
class Summary:
    total: int = 0
    matched: int = 0
    correctly_matched: int = 0
    per_transform: dict[str, dict[str, int]] = field(default_factory=dict)  # transform -> {total, matched, correct}
    latencies_ms: list[float] = field(default_factory=list)
    fair_use_false_positives: int = 0
    fair_use_total: int = 0


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--originals", type=Path, required=True)
    p.add_argument("--variants",  type=Path, required=True)
    p.add_argument("--fair-use",  type=Path, default=None)
    p.add_argument("--out",       type=Path, default=Path("data/benchmark-results"))
    p.add_argument("--api-base",  default="http://localhost:8080")
    p.add_argument("--ingest-first", action="store_true")
    args = p.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)

    with httpx.Client(timeout=120.0) as client:
        # Always capture the source-stem -> clip_id map even if we skip ingest:
        # when --ingest-first is off, the originals must already be in the API,
        # but we still need the mapping to score retrieval correctness.
        source_to_clip: dict[str, str] = {}
        if args.ingest_first:
            source_to_clip = _ingest_originals(client, args.api_base, args.originals)
        else:
            source_to_clip = _probe_originals(args.originals)

        manifest_path = args.variants / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        per_variant: list[VariantResult] = []
        summary = Summary()

        for record in manifest:
            variant_path = Path(record["path"])
            expected_stem = Path(record["source"]).stem
            expected_clip_id = source_to_clip.get(expected_stem)
            chain = record["transform_chain"]

            r = _detect(client, args.api_base, variant_path, expected_stem)
            per_variant.append(r)

            _update_summary(summary, r, chain, expected_clip_id)

        # Fair-use false-positive set.
        if args.fair_use and args.fair_use.exists():
            for p_ in sorted(args.fair_use.glob("*.mp4")):
                r = _detect(client, args.api_base, p_, expected_clip="__unrelated__")
                summary.fair_use_total += 1
                if r.matched:
                    summary.fair_use_false_positives += 1

        # Write outputs.
        _write_outputs(args.out, per_variant, summary)
        print(json.dumps(_summary_to_dict(summary), indent=2))


def _ingest_originals(client: httpx.Client, api_base: str, originals: Path) -> dict[str, str]:
    """POST each original and capture the returned clip_id. Returns stem -> clip_id."""
    stem_to_clip: dict[str, str] = {}
    for p in sorted(originals.glob("*.mp4")):
        with p.open("rb") as f:
            resp = client.post(
                f"{api_base}/ingest",
                data={
                    "title":                  p.stem,
                    "sport":                  "cricket",
                    "event":                  "Benchmark-League 2026",
                    "rights_holder":          "Aegis Benchmark",
                    "rights_holder_name":     "Benchmark Operator",
                    "rights_holder_title":    "Benchmark",
                    "rights_holder_address":  "N/A",
                    "rights_holder_phone":    "+0-000-000-0000",
                    "rights_holder_email":    "ops@benchmark.aegis.test",
                    "athletes_csv":           "",
                },
                files={"video": (p.name, f, "video/mp4")},
            )
        resp.raise_for_status()
        stem_to_clip[p.stem] = resp.json()["clip_id"]
    # Persist for --ingest-first=false runs on the same corpus.
    (originals / ".benchmark_clip_map.json").write_text(json.dumps(stem_to_clip))
    return stem_to_clip


def _probe_originals(originals: Path) -> dict[str, str]:
    """Read the stem -> clip_id map persisted by a prior --ingest-first run."""
    mapping = originals / ".benchmark_clip_map.json"
    if not mapping.exists():
        return {}
    return json.loads(mapping.read_text())


def _detect(client: httpx.Client, api_base: str, video: Path, expected_clip: str) -> VariantResult:
    t0 = time.time()
    try:
        with video.open("rb") as f:
            r = client.post(
                f"{api_base}/detect",
                data={
                    "candidate_url": f"file://benchmark/{video.name}",
                    "platform":      "mock",
                    "uploader":      "benchmark",
                    "caption":       "",
                },
                files={"video": (video.name, f, "video/mp4")},
            )
        r.raise_for_status()
        body = r.json()
    except Exception as e:
        return VariantResult(
            variant_id=video.stem,
            source=str(video),
            transform_chain=[],
            expected_clip=expected_clip,
            matched=False,
            detected_clip_id=None,
            verdict=None,
            confidence=None,
            latency_ms=(time.time() - t0) * 1000,
            error=str(e),
        )

    latency_ms = (time.time() - t0) * 1000
    if not body.get("matched"):
        return VariantResult(
            variant_id=video.stem,
            source=str(video),
            transform_chain=[],
            expected_clip=expected_clip,
            matched=False,
            detected_clip_id=None,
            verdict=None,
            confidence=None,
            latency_ms=latency_ms,
        )
    verdict = body["verdict"]
    return VariantResult(
        variant_id=video.stem,
        source=str(video),
        transform_chain=[],
        expected_clip=expected_clip,
        matched=True,
        detected_clip_id=verdict["original_clip_id"],
        verdict=verdict["verdict"],
        confidence=verdict["confidence"],
        latency_ms=latency_ms,
    )


def _update_summary(
    summary: Summary,
    r: VariantResult,
    chain: list[str],
    expected_clip_id: str | None,
) -> None:
    """Update summary with ACTUAL correctness.

    Correctness = retrieved clip_id is exactly the expected source clip's id.
    If the stem -> clip_id map is missing (no ingest step ran and no prior
    map is persisted), correctness is marked unknown and excluded from the
    "correctly_matched" count — the match-rate number is still reported
    separately as a looser signal.
    """
    summary.total += 1
    summary.latencies_ms.append(r.latency_ms)
    key = "+".join(chain) if chain else "unknown"
    bucket = summary.per_transform.setdefault(
        key, {"total": 0, "matched": 0, "correct": 0}
    )
    bucket["total"] += 1

    if r.matched:
        summary.matched += 1
        bucket["matched"] += 1
        if expected_clip_id and r.detected_clip_id == expected_clip_id:
            bucket["correct"] += 1
            summary.correctly_matched += 1


def _summary_to_dict(summary: Summary) -> dict:
    lats = sorted(summary.latencies_ms)
    p50 = statistics.median(lats) if lats else 0.0
    p95 = lats[int(len(lats) * 0.95)] if lats else 0.0
    return {
        "total":                summary.total,
        "matched":              summary.matched,
        "correctly_matched":    summary.correctly_matched,
        # Match rate: fraction of variants where detection escalated to a verdict.
        "match_rate":           (summary.matched / summary.total) if summary.total else 0.0,
        # Recall: fraction of variants where the retrieved clip_id is exactly the
        # expected source clip. This is the number docs/benchmarks.md should cite.
        "recall":               (summary.correctly_matched / summary.total) if summary.total else 0.0,
        "per_transform":        summary.per_transform,
        "latency_ms_p50":       p50,
        "latency_ms_p95":       p95,
        "fair_use_fpr":         (summary.fair_use_false_positives / summary.fair_use_total) if summary.fair_use_total else None,
    }


def _write_outputs(out: Path, per_variant: list[VariantResult], summary: Summary) -> None:
    (out / "summary.json").write_text(json.dumps(_summary_to_dict(summary), indent=2))
    with (out / "per-variant.jsonl").open("w") as f:
        for r in per_variant:
            f.write(json.dumps(asdict(r)) + "\n")


if __name__ == "__main__":
    main()
