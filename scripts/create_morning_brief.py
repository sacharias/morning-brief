#!/usr/bin/env python3
"""Create the dated morning brief as app JSON under public/data/."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config.toml"
DATA_DIR = ROOT / "public" / "data"


def load_config() -> dict:
    if not CONFIG_PATH.exists() or tomllib is None:
        return {}
    with CONFIG_PATH.open("rb") as handle:
        return tomllib.load(handle)


def run_json(command: list[str], timeout: int) -> dict:
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(detail or f"Command failed: {' '.join(command)}")
    return json.loads(result.stdout)


def run_json_safe(command: list[str], timeout: int, fallback: dict, label: str) -> dict:
    try:
        return run_json(command, timeout=timeout)
    except Exception as error:
        data = dict(fallback)
        notes = list(data.get("access_notes", []))
        notes.append(f"{label} failed: {error}")
        data["access_notes"] = notes
        return data


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def tweet_metrics(item: dict) -> list[dict]:
    metrics = []
    for label, key in (
        ("likes", "favorite_count"),
        ("reposts", "retweet_count"),
        ("replies", "reply_count"),
        ("quotes", "quote_count"),
        ("bookmarks", "bookmark_count"),
    ):
        value = item.get(key)
        if isinstance(value, int) and value:
            metrics.append({"label": label, "value": f"{value:,}"})
    return metrics


def tweet_item(item: dict) -> dict:
    author = item.get("author_screen_name") or item.get("author_name") or "x"
    return {
        "title": f"@{author}",
        "url": item.get("url", ""),
        "body": clean(item.get("text", "")),
        "metrics": tweet_metrics(item),
    }


def github_item(item: dict) -> dict:
    metrics = []
    if item.get("language"):
        metrics.append({"label": "language", "value": item["language"]})
    if item.get("stars_today"):
        metrics.append({"label": "", "value": str(item["stars_today"])})
    return {
        "title": item.get("repo", "repository"),
        "url": item.get("url", ""),
        "body": clean(item.get("description", "")),
        "metrics": metrics,
    }


def custom_trending_item(item: dict) -> dict:
    metrics = [{"label": "stars 24h", "value": f"{item.get('stars_24h', 0):,}"}]
    acceleration = item.get("acceleration")
    if acceleration:
        metrics.append({"label": "acceleration", "value": f"{acceleration}x"})
    return {
        "title": item.get("repo", "repository"),
        "url": item.get("url", ""),
        "body": clean(item.get("description", "")),
        "metrics": metrics,
    }


def paper_item(item: dict) -> dict:
    return {
        "title": clean(item.get("title", "Untitled paper")),
        "url": item.get("url", ""),
        "body": clean(item.get("summary", "")),
    }


def build_brief(
    public: dict,
    custom: dict,
    x_data: dict,
    config: dict,
    generated_at: dt.datetime,
    report_date: str,
) -> dict:
    output_cfg = config.get("output", {})
    top_github = int(output_cfg.get("top_github_projects", 10))
    top_custom = int(output_cfg.get("top_custom_trending", 10))
    top_papers = int(output_cfg.get("top_huggingface_papers", 5))

    sections = [
        {
            "id": "top-x-posts",
            "shortTitle": "Top Posts",
            "title": "Top X Posts",
            "page": "x",
            "emptyMessage": "No top X posts were captured for the configured lookback window.",
            "items": [tweet_item(item) for item in x_data.get("top_x_posts", [])],
        },
        {
            "id": "github-trending",
            "shortTitle": "Trending",
            "title": "GitHub Trending",
            "page": "code",
            "description": "github.com/trending, daily + weekly + monthly merged",
            "emptyMessage": "GitHub Trending returned no parsed projects.",
            "items": [github_item(item) for item in public.get("github_trending", [])[:top_github]],
        },
        {
            "id": "custom-trending",
            "shortTitle": "Momentum",
            "title": "Momentum",
            "page": "code",
            "description": "Our algorithm: 24h star rate vs the prior week, via ClickHouse github_events.",
            "emptyMessage": "Custom trending returned no repositories.",
            "items": [custom_trending_item(item) for item in custom.get("custom_trending", [])[:top_custom]],
        },
        {
            "id": "hf-papers",
            "shortTitle": "Papers",
            "title": "Hugging Face Papers",
            "page": "papers",
            "emptyMessage": "Hugging Face Papers returned no parsed papers.",
            "items": [paper_item(item) for item in public.get("huggingface_papers", [])[:top_papers]],
        },
        {
            "id": "x-bookmarks",
            "shortTitle": "Bookmarks",
            "title": "Latest X Bookmarks",
            "page": "x",
            "emptyMessage": "No authenticated X bookmarks were captured.",
            "items": [tweet_item(item) for item in x_data.get("x_bookmarks", [])],
        },
    ]

    return {
        "date": report_date,
        "generatedAt": generated_at.isoformat(timespec="seconds"),
        "headline": "",
        "executiveSummary": [],
        "sections": sections,
        "followUps": [],
        "runNotes": [
            *public.get("access_notes", []),
            *custom.get("access_notes", []),
            *x_data.get("access_notes", []),
        ],
    }


def update_index(report_date: str) -> Path:
    index_path = DATA_DIR / "index.json"
    days: list[str] = []
    if index_path.exists():
        try:
            days = json.loads(index_path.read_text(encoding="utf-8")).get("days", [])
        except json.JSONDecodeError:
            days = []
    if report_date not in days:
        days.append(report_date)
    days = sorted(set(days), reverse=True)
    index_path.write_text(
        json.dumps({"latest": days[0], "days": days}, indent=2) + "\n",
        encoding="utf-8",
    )
    return index_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create the morning brief JSON")
    parser.add_argument("--date", help="Report date in YYYY-MM-DD. Defaults to local today.")
    parser.add_argument("--skip-x", action="store_true", help="Skip authenticated X fetch")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config()
    generated_at = dt.datetime.now().astimezone()
    report_date = args.date or generated_at.date().isoformat()

    output_cfg = config.get("output", {})
    x_threads_cfg = config.get("sources", {}).get("x_threads", {})
    public = run_json_safe(
        ["python3", "scripts/fetch_public_sources.py"],
        timeout=600,
        fallback={"github_trending": [], "huggingface_papers": []},
        label="Public source fetch",
    )
    custom = run_json_safe(
        ["python3", "scripts/fetch_custom_trending.py"],
        timeout=300,
        fallback={"custom_trending": []},
        label="Custom trending fetch",
    )

    if args.skip_x:
        x_data = {"x_bookmarks": [], "top_x_posts": [], "access": {"method": "skipped"}, "meta": {}}
    else:
        x_data = run_json_safe(
            [
                "node",
                "scripts/fetch_x_sources.cjs",
                "--bookmarks",
                str(int(output_cfg.get("latest_bookmarks", 10))),
                "--top-posts",
                str(int(output_cfg.get("top_x_threads", 20))),
                "--lookback-hours",
                str(int(x_threads_cfg.get("lookback_hours", 72))),
            ],
            timeout=420,
            fallback={
                "x_bookmarks": [],
                "top_x_posts": [],
                "access": {"method": "unavailable"},
                "meta": {},
            },
            label="X fetch",
        )

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    brief = build_brief(public, custom, x_data, config, generated_at, report_date)
    brief_path = DATA_DIR / f"{report_date}.json"
    if brief_path.exists():
        # Re-runs refresh source data but keep agent-written editorial prose.
        try:
            previous = json.loads(brief_path.read_text(encoding="utf-8"))
            for key in ("headline", "executiveSummary", "followUps"):
                if previous.get(key):
                    brief[key] = previous[key]
        except json.JSONDecodeError:
            pass
    brief_path.write_text(json.dumps(brief, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    update_index(report_date)
    print(str(brief_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
