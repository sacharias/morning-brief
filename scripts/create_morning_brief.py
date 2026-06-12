#!/usr/bin/env python3
"""Create the dated morning brief as app JSON under public/data/."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
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


def configured_path(config: dict, key: str, default: str) -> Path:
    configured = config.get(key) or default
    path = Path(str(configured)).expanduser()
    return path if path.is_absolute() else ROOT / path


def latest_index_date() -> str | None:
    index_path = DATA_DIR / "index.json"
    if not index_path.exists():
        return None
    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    latest = data.get("latest")
    if isinstance(latest, str) and latest:
        return latest
    days = data.get("days")
    if isinstance(days, list) and days:
        return str(days[0])
    return None


def validate_report_date(report_date: str) -> str:
    dt.date.fromisoformat(report_date)
    return report_date


def markdown_link(title: str, url: str) -> str:
    label = clean(title) or "Untitled"
    href = clean(url)
    if not href:
        return label
    safe_label = label.replace("[", "\\[").replace("]", "\\]")
    safe_href = href.replace(">", "%3E")
    return f"[{safe_label}](<{safe_href}>)"


def markdown_meta(item: dict) -> str:
    parts: list[str] = []
    metrics = item.get("metrics")
    if isinstance(metrics, list):
        formatted = []
        for metric in metrics:
            if not isinstance(metric, dict):
                continue
            label = clean(metric.get("label", ""))
            value = clean(metric.get("value", ""))
            if label and value:
                formatted.append(f"{label}: {value}")
            elif value:
                formatted.append(value)
        if formatted:
            parts.append("; ".join(formatted))
    tags = item.get("tags")
    if isinstance(tags, list):
        cleaned_tags = [clean(tag) for tag in tags if clean(tag)]
        if cleaned_tags:
            parts.append("tags: " + ", ".join(cleaned_tags))
    if item.get("isNew"):
        parts.append("new")
    previously = item.get("previously")
    if isinstance(previously, list) and previously:
        dates = [clean(entry.get("date", "")) for entry in previously if isinstance(entry, dict)]
        dates = [date for date in dates if date]
        if dates:
            parts.append("previously: " + ", ".join(dates))
    return " | ".join(parts)


def render_markdown_report(brief: dict, config: dict) -> str:
    title = clean(config.get("brief_title", "Morning Brief")) or "Morning Brief"
    report_date = clean(brief.get("date", "unknown-date"))
    generated_at = clean(brief.get("generatedAt", ""))

    lines = [f"# {title} - {report_date}", ""]
    if generated_at:
        lines.extend([f"Generated: {generated_at}", ""])

    headline = clean(brief.get("headline", ""))
    lines.extend(["## Headline", "", headline or "No headline written yet.", ""])

    lines.extend(["## Executive Summary", ""])
    summary = brief.get("executiveSummary")
    if isinstance(summary, list) and summary:
        for item in summary:
            text = clean(str(item))
            if text:
                lines.append(f"- {text}")
    else:
        lines.append("- No executive summary written yet.")
    lines.append("")

    sections = brief.get("sections")
    if isinstance(sections, list):
        for section in sections:
            if not isinstance(section, dict):
                continue
            section_title = clean(section.get("title", "")) or clean(section.get("id", "")) or "Section"
            lines.extend([f"## {section_title}", ""])
            description = clean(section.get("description", ""))
            if description:
                lines.extend([description, ""])
            items = section.get("items")
            if not isinstance(items, list) or not items:
                lines.extend([clean(section.get("emptyMessage", "")) or "No items.", ""])
                continue
            for index, item in enumerate(items, start=1):
                if not isinstance(item, dict):
                    continue
                lines.append(f"{index}. {markdown_link(item.get('title', ''), item.get('url', ''))}")
                body = clean(item.get("body", ""))
                if body:
                    lines.append(f"   {body}")
                meta = markdown_meta(item)
                if meta:
                    lines.append(f"   Meta: {meta}")
                lines.append("")

    follow_ups = brief.get("followUps")
    lines.extend(["## Follow-ups", ""])
    if isinstance(follow_ups, list) and follow_ups:
        for item in follow_ups:
            text = clean(str(item))
            if text:
                lines.append(f"- {text}")
    else:
        lines.append("- No follow-ups written yet.")
    lines.append("")

    run_notes = brief.get("runNotes")
    lines.extend(["## Run Notes", ""])
    if isinstance(run_notes, list) and run_notes:
        for item in run_notes:
            text = clean(str(item))
            if text:
                lines.append(f"- {text}")
    else:
        lines.append("- No run notes.")
    lines.append("")
    return "\n".join(lines)


def write_markdown_report(brief: dict, config: dict) -> Path:
    output_cfg = config.get("output", {})
    report_format = str(output_cfg.get("report_format", "markdown")).lower()
    if report_format not in ("markdown", "md"):
        raise ValueError(f"Unsupported report_format: {report_format}. Use 'markdown'.")
    report_date = validate_report_date(str(brief.get("date", "")))
    report_dir = configured_path(config, "report_directory", "reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{report_date}.md"
    report_path.write_text(render_markdown_report(brief, config), encoding="utf-8")
    return report_path


def assert_directory_writable(directory: Path, label: str) -> None:
    probe = directory / ".write-test"
    try:
        directory.mkdir(parents=True, exist_ok=True)
        probe.write_text("", encoding="utf-8")
    except OSError as error:
        raise RuntimeError(
            f"{label} is not writable: {directory}. "
            "Run the morning brief from a writable checkout with a writable temp directory."
        ) from error
    finally:
        try:
            probe.unlink()
        except OSError:
            pass


def preflight_environment(config: dict, save_report: bool) -> list[Path]:
    paths = [DATA_DIR]
    if save_report:
        paths.append(configured_path(config, "report_directory", "reports"))
    temp_dir = Path(os.environ.get("MORNING_BRIEF_TMPDIR") or os.environ.get("TMPDIR") or ROOT / "tmp").expanduser()
    if not temp_dir.is_absolute():
        temp_dir = ROOT / temp_dir
    paths.append(temp_dir)

    checked: list[Path] = []
    for path in paths:
        label = "Output directory" if path == DATA_DIR else "Report directory" if path.name == "reports" else "Temporary directory"
        assert_directory_writable(path, label)
        checked.append(path)
    return checked


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
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Write reports/YYYY-MM-DD.md from an existing JSON day file without fetching sources.",
    )
    parser.add_argument("--no-report", action="store_true", help="Do not write the Markdown sidecar report.")
    parser.add_argument(
        "--preflight",
        action="store_true",
        help="Check output and temporary directories are writable, then exit.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config()
    generated_at = dt.datetime.now().astimezone()
    report_date = validate_report_date(
        args.date or (latest_index_date() if args.report_only else None) or generated_at.date().isoformat()
    )
    output_cfg = config.get("output", {})
    save_report = output_cfg.get("save_report", True) and not args.no_report

    if args.preflight:
        for path in preflight_environment(config, save_report):
            print(f"writable: {path}")
        return 0

    if args.report_only:
        brief_path = DATA_DIR / f"{report_date}.json"
        if not brief_path.exists():
            raise FileNotFoundError(f"No day file found: {brief_path}")
        brief = json.loads(brief_path.read_text(encoding="utf-8"))
        report_path = write_markdown_report(brief, config)
        print(str(report_path))
        return 0

    sources_cfg = config.get("sources", {})
    preflight_environment(config, save_report)

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
    index_path = update_index(report_date)
    print(str(brief_path))
    print(str(index_path))
    if save_report:
        print(str(write_markdown_report(brief, config)))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
