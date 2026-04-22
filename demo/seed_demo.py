"""Reproducible flagship demo scenario driver.

Given a running Aegis API (LOCAL or GCP mode), this script executes the
full "Test-Subject Meera" walkthrough from docs/case-study.md:

    1. Ingest: publish the original clip (signed, fingerprinted, indexed).
    2. Leak:   submit the manipulated clip as a candidate via /detect.
    3. Classify: API returns a DEEPFAKE_MANIPULATION verdict.
    4. Alert:  the athlete-facing view picks up the verdict (manual eyeball).
    5. Takedown: draft + file jurisdiction-aware notices across all 4 mocks.
    6. Verify:  fetch the Merkle-anchored receipt from /verify/{detection_id}.

Usage:
    python demo/seed_demo.py \
        --original  data/originals/test-subject-meera-clean.mp4 \
        --leak      data/case-study/generated/constructed-meera-clip.mp4 \
        --api-base  http://localhost:8080

Prints a JSON summary with the detection_id, jurisdiction chosen, takedown
platforms hit, and the Merkle root. The ./demo/script.md storyboard calls
out the exact lines of this output to show on-screen.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--original", type=Path, required=True)
    p.add_argument("--leak",     type=Path, required=True)
    p.add_argument("--api-base", default="http://localhost:8080")
    p.add_argument("--platforms", default="telegram,x,meta,youtube",
                   help="Comma-separated list to target. Demo shows all four.")
    args = p.parse_args()

    for path in (args.original, args.leak):
        if not path.exists():
            print(f"missing: {path}", file=sys.stderr)
            return 2

    summary: dict = {"steps": []}

    with httpx.Client(base_url=args.api_base, timeout=120.0) as client:
        # 1. Publish the original.
        with args.original.open("rb") as f:
            r = client.post(
                "/ingest",
                data={
                    "title":                 "Test-Subject Meera vs Test-League — Over 14",
                    "sport":                 "cricket",
                    "event":                 "Test-League 2026 · Match 4 (fictional)",
                    "rights_holder":         "Test-League Broadcasting (fictional)",
                    "rights_holder_name":    "Demo Operator",
                    "rights_holder_title":   "Demo",
                    "rights_holder_address": "N/A",
                    "rights_holder_phone":   "+0-000-000-0000",
                    "rights_holder_email":   "demo@aegis.test",
                    "athletes_csv":          "test-subject-meera",
                },
                files={"video": (args.original.name, f, "video/mp4")},
            )
        r.raise_for_status()
        clip_id = r.json()["clip_id"]
        summary["steps"].append({"step": "ingest", "clip_id": clip_id})

        # 2. Leak lands in each configured platform. We loop to show the pipeline
        #    handles per-platform jurisdiction routing correctly in one run.
        detection_ids: list[str] = []
        for platform in [p_.strip() for p_ in args.platforms.split(",") if p_.strip()]:
            with args.leak.open("rb") as f:
                r = client.post(
                    "/detect",
                    data={
                        "candidate_url": f"https://aegis-test-domain.example/{platform}/meera-leak.mp4",
                        "platform":      platform,
                        "uploader":      f"bad-actor-{platform}",
                        "caption":       "Test-Subject Meera — morphed / deepfake clip",
                        "host_country":  "IN" if platform == "telegram" else "",
                    },
                    files={"video": (args.leak.name, f, "video/mp4")},
                )
            r.raise_for_status()
            body = r.json()
            if not body.get("matched"):
                summary["steps"].append({"step": "detect", "platform": platform, "matched": False})
                continue
            d_id = body["verdict"]["detection_id"]
            detection_ids.append(d_id)
            summary["steps"].append({
                "step":         "detect",
                "platform":     platform,
                "detection_id": d_id,
                "verdict":      body["verdict"]["verdict"],
                "confidence":   body["verdict"]["confidence"],
                "recommended_action": body["verdict"]["recommended_action"],
            })

        # 3. Takedown for each detection.
        takedowns: list[dict] = []
        for d_id in detection_ids:
            r = client.post("/takedown", json={"detection_id": d_id, "file_now": True})
            if r.status_code == 409:
                takedowns.append({"detection_id": d_id, "skipped": "below-threshold"})
                continue
            r.raise_for_status()
            notice = r.json()["notice"]
            takedowns.append({
                "detection_id":  d_id,
                "jurisdiction": notice["jurisdiction"],
                "platform":      notice["platform"],
                "status":        notice["status"],
                "ticket_id":     notice.get("platform_ticket_id"),
                "subject":       notice["subject"],
            })
        summary["steps"].append({"step": "takedown", "filings": takedowns})

        # 4. Verify — pull the Merkle receipt for the first detection.
        if detection_ids:
            r = client.get(f"/verify/{detection_ids[0]}")
            r.raise_for_status()
            v = r.json()
            summary["steps"].append({
                "step":           "verify",
                "detection_id":   detection_ids[0],
                "verdict":        v["verdict"],
                "merkle_root":    v["merkle_receipt"]["merkle_root_hex"] if v.get("merkle_receipt") else None,
                "kms_key_version": v["merkle_receipt"]["kms_key_version"] if v.get("merkle_receipt") else None,
            })

    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
