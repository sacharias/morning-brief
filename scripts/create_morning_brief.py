#!/usr/bin/env python3
"""Create a dated Markdown morning brief report."""

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


def truncate(text: str, limit: int = 220) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def metric_summary(item: dict) -> str:
    parts = []
    for label, key in (
        ("likes", "favorite_count"),
        ("reposts", "retweet_count"),
        ("replies", "reply_count"),
        ("quotes", "quote_count"),
        ("bookmarks", "bookmark_count"),
    ):
        value = item.get(key)
        if isinstance(value, int) and value:
            parts.append(f"{value:,} {label}")
    score = engagement_score(item)
    if score:
        parts.append(f"engagement score {score:,}")
    return ", ".join(parts) if parts else "metrics unavailable"


def engagement_score(item: dict) -> int:
    score = item.get("score")
    if isinstance(score, int):
        return score
    return (
        int(item.get("favorite_count") or 0)
        + 2 * int(item.get("retweet_count") or 0)
        + 2 * int(item.get("quote_count") or 0)
        + int(item.get("reply_count") or 0)
        + int(item.get("bookmark_count") or 0)
    )


def tweet_line(item: dict, why: str) -> str:
    author = item.get("author_screen_name") or item.get("author_name") or "x"
    text = truncate(item.get("text", ""))
    return (
        f"- [@{author}]({item.get('url', '')}) - {text}\n"
        f"  - Why it matters: {why}\n"
        f"  - Signal: {metric_summary(item)}"
    )


def github_line(item: dict) -> str:
    desc = truncate(item.get("description", ""), 180)
    meta = ", ".join(part for part in (item.get("language"), item.get("stars_today")) if part)
    suffix = f" ({meta})" if meta else ""
    return f"- [{item.get('repo')}]({item.get('url')}){suffix} - {desc}"


def paper_line(item: dict) -> str:
    return f"- [{item.get('title')}]({item.get('url')})"


def build_markdown(public: dict, x_data: dict, config: dict, generated_at: dt.datetime) -> str:
    output_cfg = config.get("output", {})
    top_github = int(output_cfg.get("top_github_projects", 5))
    top_papers = int(output_cfg.get("top_huggingface_papers", 5))

    bookmarks = x_data.get("x_bookmarks", [])
    top_posts = x_data.get("top_x_posts", [])
    github = public.get("github_trending", [])[:top_github]
    papers = public.get("huggingface_papers", [])[:top_papers]
    access = x_data.get("access", {})
    meta = x_data.get("meta", {})
    lookback_hours = int(meta.get("lookback_hours") or config.get("sources", {}).get("x_threads", {}).get("lookback_hours", 72))
    capture_summary = "; ".join(
        f"{item.get('op')} HTTP {item.get('status')} ({item.get('tweets')} tweets)"
        for item in meta.get("capture_summary", [])
    )

    lines = [
        f"# Morning Brief - {generated_at.date().isoformat()}",
        "",
        f"Generated: {generated_at.strftime('%Y-%m-%d %H:%M %Z')}",
        "",
        "## Executive Summary",
        "",
        f"- X authenticated access worked through a temporary Chrome profile; captured {len(bookmarks)} bookmarks and {len(top_posts)} top posts.",
        f"- Public sources were fetched with simple HTTP: {len(github)} GitHub Trending repos and {len(papers)} Hugging Face papers.",
        f"- Top X posts are filtered to the last {lookback_hours} hours and sorted by engagement score: likes + bookmarks + replies + 2x reposts + 2x quotes.",
        "",
        "## Latest X Bookmarks",
        "",
    ]

    if bookmarks:
        for item in bookmarks:
            lines.append(tweet_line(item, "You explicitly saved it, so it is worth revisiting for tactics, tools, or product ideas."))
    else:
        lines.append("- No authenticated X bookmarks were captured.")

    lines.extend(["", "## Top X Posts", ""])
    if top_posts:
        for item in top_posts:
            lines.append(tweet_line(item, f"It ranked highly in the last-{lookback_hours}-hour AI, business, and startup searches by engagement score."))
    else:
        lines.append("- No top X posts were captured for the configured lookback window.")

    lines.extend(["", "## Trending GitHub Projects", ""])
    if github:
        lines.extend(github_line(item) for item in github)
    else:
        lines.append("- GitHub Trending returned no parsed projects.")

    lines.extend(["", "## Hugging Face Papers", ""])
    if papers:
        lines.extend(paper_line(item) for item in papers)
    else:
        lines.append("- Hugging Face Papers returned no parsed papers.")

    lines.extend([
        "",
        "## Recommended Follow-Ups",
        "",
        "- Open the highest-signal saved X items and decide whether they should become skills, prompts, or product research notes.",
        "- Check the top GitHub projects for installability, license, and whether they map to active automation ideas.",
        "- Skim the Hugging Face papers for anything that changes model, eval, or agent workflow assumptions.",
        "",
        "## Sources And Access Notes",
        "",
        f"- X: `{access.get('method', 'unknown')}`, Chrome profile `{access.get('chrome_profile', 'unknown')}`.",
        f"- X operations: `{json.dumps(access.get('operation_ids', {}), sort_keys=True)}`.",
        f"- X capture summary: {capture_summary or 'none'}.",
        "- GitHub Trending: `python3 scripts/fetch_public_sources.py` via `curl`.",
        "- Hugging Face Papers: `python3 scripts/fetch_public_sources.py` via `curl`.",
        "",
    ])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create the morning brief report")
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
    public = run_json(["python3", "scripts/fetch_public_sources.py"], timeout=60)

    if args.skip_x:
        x_data = {"x_bookmarks": [], "top_x_posts": [], "access": {"method": "skipped"}, "meta": {}}
    else:
        x_data = run_json(
            [
                "node",
                "scripts/fetch_x_sources.js",
                "--bookmarks",
                str(int(output_cfg.get("latest_bookmarks", 10))),
                "--top-posts",
                str(int(output_cfg.get("top_x_threads", 20))),
                "--lookback-hours",
                str(int(x_threads_cfg.get("lookback_hours", 72))),
            ],
            timeout=180,
        )

    report_dir = ROOT / config.get("report_directory", "reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{report_date}.md"
    report_path.write_text(build_markdown(public, x_data, config, generated_at), encoding="utf-8")
    print(str(report_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
