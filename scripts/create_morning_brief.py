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
LEDGER_PATH = ROOT / "state" / "idea_ledger.json"


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


def founder_signal_item(item: dict) -> dict:
    built = {
        "title": clean(item.get("title", "")),
        "url": item.get("url", ""),
        "body": clean(item.get("body", "")),
    }
    metrics = []
    for label in ("points", "comments"):
        value = item.get(label)
        if isinstance(value, int) and value:
            metrics.append({"label": label, "value": f"{value:,}"})
    if metrics:
        built["metrics"] = metrics
    if item.get("source"):
        built["tags"] = [item["source"]]
    return built


def shipped_item(item: dict) -> dict:
    built = {
        "title": clean(item.get("title", "")),
        "url": item.get("url", ""),
        "body": clean(item.get("body", "")),
    }
    if item.get("source"):
        built["tags"] = [item["source"]]
    return built


def load_ledger_ideas() -> list[dict]:
    """Open + validated ledger ideas, newest-updated first; tolerates a missing or invalid file."""
    try:
        data = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    ideas = data.get("ideas", []) if isinstance(data, dict) else []
    if not isinstance(ideas, list):
        return []
    kept = [
        idea
        for idea in ideas
        if isinstance(idea, dict) and idea.get("status") in ("open", "validated")
    ]
    kept.sort(key=lambda idea: (idea.get("updated") or idea.get("created") or ""), reverse=True)
    return kept


def idea_item(idea: dict, report_date: str) -> dict:
    try:
        created = dt.date.fromisoformat(idea.get("created") or report_date)
        day_count = (dt.date.fromisoformat(report_date) - created).days + 1
    except ValueError:
        day_count = 1
    built = {
        "title": clean(idea.get("title", "Untitled idea")),
        "body": clean(idea.get("summary", "")),
        "tags": [idea.get("status", "open"), f"day {max(day_count, 1)}"],
    }
    urls = list(
        dict.fromkeys(
            evidence.get("url")
            for evidence in idea.get("evidence", [])
            if isinstance(evidence, dict) and evidence.get("url")
        )
    )
    if len(urls) == 1:
        built["url"] = urls[0]
    return built


def item_key(item: dict) -> str:
    return (item.get("url") or item.get("title") or "").strip().rstrip("/")


def previous_appearances(report_date: str) -> dict[str, list[str]] | None:
    """Item key → sorted dates seen across the last 5 earlier day files, or None without a baseline."""
    days = sorted(
        path.stem
        for path in DATA_DIR.glob("????-??-??.json")
        if path.stem < report_date
    )[-5:]
    if not days:
        return None
    seen: dict[str, set[str]] = {}
    for day in days:
        try:
            previous = json.loads((DATA_DIR / f"{day}.json").read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        for section in previous.get("sections", []):
            for item in section.get("items", []):
                key = item_key(item)
                if key:
                    seen.setdefault(key, set()).add(day)
    return {key: sorted(dates) for key, dates in seen.items()}


def mark_continuity(sections: list[dict], appearances: dict[str, list[str]] | None) -> None:
    """Flag unseen items as new; recurring items carry `previously` (newest first), never both."""
    # Without an earlier day there is no baseline; skip flags rather than mark everything.
    if appearances is None:
        return
    for section in sections:
        for item in section.get("items", []):
            key = item_key(item)
            if not key:
                continue
            dates = appearances.get(key)
            if dates:
                item["previously"] = [{"date": date} for date in reversed(dates)]
                item.pop("isNew", None)
            else:
                item["isNew"] = True


def developing_section(sections: list[dict]) -> dict | None:
    """Scaffold of stories recurring on ≥2 earlier days; the agent rewrites each body as a delta."""
    items: list[dict] = []
    seen: set[str] = set()
    for section in sections:
        for item in section.get("items", []):
            key = item_key(item)
            if not key or key in seen or len(item.get("previously", [])) < 2:
                continue
            seen.add(key)
            items.append(
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "body": item.get("body", ""),
                    "previously": item["previously"],
                }
            )
            if len(items) == 5:
                break
        if len(items) == 5:
            break
    if not items:
        return None
    return {
        "id": "developing",
        "title": "Developing",
        "page": "today",
        "emptyMessage": "No stories are recurring across recent briefs.",
        "items": items,
    }


def build_brief(
    public: dict,
    custom: dict,
    x_data: dict,
    founder: dict,
    shipped: dict,
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
        {
            "id": "build-ideas",
            "shortTitle": "Ideas",
            "title": "Build Ideas",
            "page": "build",
            "description": "Open and validated ideas from the ledger, newest first.",
            "emptyMessage": "The idea ledger is empty — synthesize 1–2 ideas from today's asks, proof, and shipped capabilities.",
            "previewCount": 6,
            "items": [idea_item(idea, report_date) for idea in load_ledger_ideas()],
        },
        {
            "id": "demand-signals",
            "shortTitle": "Asks",
            "title": "Demand Signals",
            "page": "build",
            "description": "What people want: pain points and \"I'd pay for\" posts from HN and Reddit.",
            "emptyMessage": "No request-shaped posts cleared the bar in the lookback window.",
            "previewCount": 6,
            "items": [founder_signal_item(item) for item in founder.get("demand_signals", [])],
        },
        {
            "id": "revenue-proof",
            "shortTitle": "Proof",
            "title": "Revenue Proof",
            "page": "build",
            "description": "What people pay for: MRR milestones, sales, and acquisition posts.",
            "emptyMessage": "No revenue milestones surfaced in the lookback window.",
            "previewCount": 6,
            "items": [founder_signal_item(item) for item in founder.get("revenue_proof", [])],
        },
        {
            "id": "launches",
            "shortTitle": "Launches",
            "title": "Launches",
            "page": "build",
            "description": "What's already taken: today's Product Hunt launches.",
            "emptyMessage": "No launches were captured from Product Hunt.",
            "previewCount": 6,
            "items": [founder_signal_item(item) for item in founder.get("launches", [])],
        },
        {
            "id": "shipped",
            "shortTitle": "Shipped",
            "title": "Shipped",
            "page": "code",
            "description": "What just became possible: vendor releases, trending models, SDK releases.",
            "emptyMessage": "No vendor releases or SDK updates landed in the lookback window.",
            "previewCount": 8,
            "items": [shipped_item(item) for item in shipped.get("shipped", [])],
        },
    ]

    mark_continuity(sections, previous_appearances(report_date))
    developing = developing_section(sections)
    if developing:
        sections.insert(0, developing)

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
            *founder.get("access_notes", []),
            *shipped.get("access_notes", []),
        ],
    }


def preserve_agent_sections(brief: dict, previous: dict) -> None:
    """Keep agent-authored developing/build-ideas sections from an earlier run wholesale."""
    for section_id in ("developing", "build-ideas"):
        existing = next(
            (section for section in previous.get("sections", []) if section.get("id") == section_id),
            None,
        )
        if not existing:
            continue
        items = existing.get("items", [])
        if not items or not any((item.get("body") or "").strip() for item in items):
            continue
        sections = brief["sections"]
        index = next(
            (position for position, section in enumerate(sections) if section.get("id") == section_id),
            None,
        )
        if index is not None:
            sections[index] = existing
        elif section_id == "developing":
            sections.insert(0, existing)
        else:
            sections.append(existing)


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
    sources_cfg = config.get("sources", {})
    x_threads_cfg = sources_cfg.get("x_threads", {})
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

    founder_fallback = {"demand_signals": [], "revenue_proof": [], "launches": []}
    if sources_cfg.get("founder_signals", {}).get("enabled", True):
        founder = run_json_safe(
            ["python3", "scripts/fetch_founder_signals.py"],
            timeout=300,
            fallback=founder_fallback,
            label="Founder signals fetch",
        )
    else:
        founder = {
            **founder_fallback,
            "access_notes": ["Founder signals disabled in config.toml; fetch skipped."],
        }

    if sources_cfg.get("shipped", {}).get("enabled", True):
        shipped = run_json_safe(
            ["python3", "scripts/fetch_shipped.py"],
            timeout=300,
            fallback={"shipped": []},
            label="Shipped fetch",
        )
    else:
        shipped = {
            "shipped": [],
            "access_notes": ["Shipped sources disabled in config.toml; fetch skipped."],
        }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    brief = build_brief(public, custom, x_data, founder, shipped, config, generated_at, report_date)
    brief_path = DATA_DIR / f"{report_date}.json"
    if brief_path.exists():
        # Re-runs refresh source data but keep agent-written editorial prose.
        try:
            previous = json.loads(brief_path.read_text(encoding="utf-8"))
            for key in ("headline", "executiveSummary", "followUps"):
                if previous.get(key):
                    brief[key] = previous[key]
            preserve_agent_sections(brief, previous)
        except json.JSONDecodeError:
            pass
    brief_path.write_text(json.dumps(brief, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    update_index(report_date)
    print(str(brief_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
