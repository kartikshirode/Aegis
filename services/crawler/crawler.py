"""Aegis crawler.

Finds candidate sports-media clips at publicly reachable URLs, respecting
robots.txt, and posts each to the Aegis API's POST /detect endpoint for
two-stage detection.

## Legal posture

- Public URLs only. No authentication, no cookie replay, no captcha solving.
- robots.txt is fetched once per host and honored. Disallowed paths are skipped.
- Rate-limited per host (default: 1 req/s). No burst.
- User-Agent: "AegisCrawler/0.1 (+https://github.com/aegis-team/aegis)".
- Respects Retry-After on 429 / 503.
- Seeds are operator-provided. The crawler does not discover new hosts on its own in Phase-1.

## Phase-1 reality

Seeds come from a JSON file:
    [
        {"host": "aegis-test-domain.example", "seeds": ["https://.../clip-1", ...]},
        ...
    ]
For the demo, the seeds list is one URL on our honeypot test domain.

## Phase-2 direction

Move to Cloud Run Jobs with Pub/Sub fan-out, add a URL-frontier over BigQuery,
and switch seed management to a Firestore collection so operators can add seeds
via the rights-holder dashboard.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import mimetypes
import os
import time
import urllib.parse
import urllib.robotparser
from dataclasses import dataclass
from pathlib import Path

import httpx

log = logging.getLogger("aegis.crawler")

USER_AGENT = "AegisCrawler/0.1 (+https://github.com/aegis-team/aegis)"
DEFAULT_RATE_DELAY_SECONDS = 1.0
VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".webm"}


@dataclass
class Seed:
    host: str
    urls: list[str]


def load_seeds(path: Path) -> list[Seed]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [Seed(host=d["host"], urls=list(d.get("seeds", []))) for d in data]


class RobotsCache:
    def __init__(self) -> None:
        self._parsers: dict[str, urllib.robotparser.RobotFileParser] = {}

    def allowed(self, url: str) -> bool:
        parts = urllib.parse.urlsplit(url)
        if not parts.scheme or not parts.netloc:
            return False
        base = f"{parts.scheme}://{parts.netloc}"
        if base not in self._parsers:
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(f"{base}/robots.txt")
            try:
                rp.read()
            except Exception:
                # If robots.txt is unreachable we default to conservative (not allowed).
                rp = _disallow_all_parser()
            self._parsers[base] = rp
        return self._parsers[base].can_fetch(USER_AGENT, url)


def _disallow_all_parser() -> urllib.robotparser.RobotFileParser:
    rp = urllib.robotparser.RobotFileParser()
    rp.parse(["User-agent: *", "Disallow: /"])
    return rp


def looks_like_video(url: str, resp_headers: dict) -> bool:
    ext = os.path.splitext(urllib.parse.urlsplit(url).path)[1].lower()
    if ext in VIDEO_EXTENSIONS:
        return True
    ctype = resp_headers.get("content-type", "").lower()
    return ctype.startswith("video/") or ctype == "application/octet-stream"


def crawl(seeds: list[Seed], out_dir: Path, *, api_base: str, rate_delay: float = DEFAULT_RATE_DELAY_SECONDS) -> list[dict]:
    """Crawl seed URLs, download likely-video responses, and submit to the API."""
    out_dir.mkdir(parents=True, exist_ok=True)
    robots = RobotsCache()
    results: list[dict] = []

    with httpx.Client(headers={"User-Agent": USER_AGENT}, follow_redirects=True, timeout=15.0) as client:
        for seed in seeds:
            for url in seed.urls:
                if not robots.allowed(url):
                    log.info("robots disallow: %s", url)
                    continue
                try:
                    resp = client.get(url)
                except httpx.HTTPError as e:
                    log.warning("fetch failed: %s -- %s", url, e)
                    continue

                if resp.status_code in (429, 503):
                    retry_after = float(resp.headers.get("retry-after", "5"))
                    log.info("rate-limited: %s sleep %s", url, retry_after)
                    time.sleep(retry_after)
                    continue

                if resp.status_code != 200:
                    log.info("non-200 %s: %s", resp.status_code, url)
                    continue

                if not looks_like_video(url, dict(resp.headers)):
                    log.info("skip non-video: %s", url)
                    continue

                # Persist + submit
                digest = hashlib.sha256(resp.content).hexdigest()[:16]
                ext = os.path.splitext(urllib.parse.urlsplit(url).path)[1] or ".mp4"
                dst = out_dir / f"candidate_{digest}{ext}"
                dst.write_bytes(resp.content)

                submission = _submit_to_aegis(client, api_base, url, seed.host, dst, resp.headers)
                results.append({"url": url, "local": str(dst), "aegis": submission})

                time.sleep(rate_delay)

    return results


def _submit_to_aegis(
    client: httpx.Client,
    api_base: str,
    url: str,
    host: str,
    local_path: Path,
    resp_headers,
) -> dict:
    platform = _platform_from_host(host)
    host_country = _country_from_host(host)
    with local_path.open("rb") as f:
        r = client.post(
            f"{api_base.rstrip('/')}/detect",
            data={
                "candidate_url": url,
                "platform":      platform,
                "uploader":      _uploader_from_headers(resp_headers),
                "caption":       resp_headers.get("content-disposition", "")[:256],
                "host_country":  host_country or "",
            },
            files={"video": (local_path.name, f, _mime(local_path))},
            timeout=60.0,
        )
    r.raise_for_status()
    return r.json()


def _platform_from_host(host: str) -> str:
    h = host.lower()
    if "twitter" in h or "x.com" in h:   return "x"
    if "youtube" in h or "youtu.be" in h: return "youtube"
    if "facebook" in h or "instagram" in h: return "meta"
    if "telegram" in h or "t.me" in h:   return "telegram"
    return "other"


def _country_from_host(host: str) -> str | None:
    # Phase-1 heuristic — GeoIP would be the real path.
    return None


def _uploader_from_headers(h) -> str:
    return h.get("x-uploader", "unknown")


def _mime(path: Path) -> str:
    return mimetypes.guess_type(str(path))[0] or "video/mp4"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=Path, required=True, help="Path to seeds.json")
    p.add_argument("--out", type=Path, default=Path("data/candidates"))
    p.add_argument("--api-base", default=os.environ.get("AEGIS_API_BASE", "http://localhost:8080"))
    p.add_argument("--rate-delay", type=float, default=DEFAULT_RATE_DELAY_SECONDS)
    p.add_argument("--log-level", default="INFO")
    args = p.parse_args()

    logging.basicConfig(level=args.log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s")

    seeds = load_seeds(args.seeds)
    results = crawl(seeds, args.out, api_base=args.api_base, rate_delay=args.rate_delay)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
