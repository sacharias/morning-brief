#!/usr/bin/env python3
"""Validate a published morning brief against the editorial quality gate."""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config.toml"
DATA_DIR = ROOT / "public" / "data"

VERDICTS = {"act", "watch", "ignore"}
SO_WHAT = re.compile(
    r"\b(because|means|matters|unlocks|validates|signals|shows|lets|helps|"
    r"forces|reduces|creates|turns|points|useful|worth|action|buyer|pain|risk|"
    r"cost|revenue|demand|workflow|builder)\b",
    re.I,
)
WEAK_REPEAT = re.compile(r"\b(still trending|still relevant|still popular|remains relevant|continues to get attention)\b", re.I)
DELTA = re.compile(r"\b(what changed|new today|now|since|delta|added|launched|released|changed|updated|crossed|evidence)\b", re.I)


def load_config() -> dict:
    if not CONFIG_PATH.exists() or tomllib is None:
        return {}
    with CONFIG_PATH.open("rb") as handle:
        return tomllib.load(handle)


def load_day(day: str | None) -> tuple[str, dict]:
    if not day:
        index = json.loads((DATA_DIR / "index.json").read_text(encoding="utf-8"))
        day = index.get("latest") or (index.get("days") or [None])[0]
    if not day:
        raise FileNotFoundError("No brief date supplied and public/data/index.json has no latest day.")
    path = DATA_DIR / f"{day}.json"
    return day, json.loads(path.read_text(encoding="utf-8"))


def section_map(brief: dict) -> dict[str, dict]:
    return {
        section.get("id", ""): section
        for section in brief.get("sections", [])
        if isinstance(section, dict)
    }


def section_items(section: dict | None) -> list[dict]:
    items = section.get("items", []) if isinstance(section, dict) else []
    return [item for item in items if isinstance(item, dict)]


def host(url: str) -> str:
    try:
        return urllib.parse.urlparse(url).netloc.lower().removeprefix("www.")
    except Exception:
        return ""


def item_label(section_id: str, index: int, item: dict) -> str:
    title = item.get("title") or item.get("url") or "untitled"
    return f"{section_id}[{index + 1}] {title}"


def validate(day: str | None) -> list[str]:
    config = load_config()
    quality = config.get("quality_gate", {})
    max_total = int(quality.get("max_total_items", 60))
    max_today_blocks = int(quality.get("max_today_blocks", 10))
    hidden_count = int(quality.get("hidden_signals", 3))
    follow_up_count = int(quality.get("follow_ups", 3))

    output = config.get("output", {})
    sources = config.get("sources", {})
    section_caps = {
        "top-x-posts": int(output.get("top_x_threads", 12)),
        "github-trending": int(output.get("top_github_projects", 8)),
        "custom-trending": int(output.get("top_custom_trending", 8)),
        "hf-papers": int(output.get("top_huggingface_papers", 5)),
        "x-bookmarks": int(output.get("latest_bookmarks", 5)),
        "demand-signals": int(sources.get("founder_signals", {}).get("max_demand", 6)),
        "revenue-proof": int(sources.get("founder_signals", {}).get("max_revenue", 4)),
        "launches": int(sources.get("founder_signals", {}).get("max_launches", 5)),
        "shipped": int(sources.get("shipped", {}).get("max_items", 8)),
        "hidden-signals": hidden_count,
    }

    report_date, brief = load_day(day)
    errors: list[str] = []
    sections = section_map(brief)
    rendered_sections = [
        section for section in brief.get("sections", [])
        if isinstance(section, dict) and isinstance(section.get("items"), list)
    ]
    total_items = sum(len(section.get("items", [])) for section in rendered_sections)

    if total_items > max_total:
        errors.append(f"{report_date}: renders {total_items} items; quality gate allows {max_total}.")

    headline = str(brief.get("headline") or "").strip()
    if not headline:
        errors.append("headline is empty.")
    elif len(headline) > 190:
        errors.append("headline is too long for the morning scan.")

    summary = brief.get("executiveSummary")
    if not isinstance(summary, list) or not (3 <= len([item for item in summary if str(item).strip()]) <= 5):
        errors.append("executiveSummary must contain 3-5 non-empty bullets.")

    follow_ups = [item for item in brief.get("followUps", []) if str(item).strip()]
    if len(follow_ups) > follow_up_count:
        errors.append(f"followUps has {len(follow_ups)} items; cap is {follow_up_count}.")

    hidden = section_items(sections.get("hidden-signals"))
    if len(hidden) != hidden_count:
        errors.append(f"hidden-signals must contain exactly {hidden_count} items; found {len(hidden)}.")

    today_blocks = 2 + (len(summary) if isinstance(summary, list) else 0) + len(hidden) + min(len(follow_ups), follow_up_count)
    if today_blocks > max_today_blocks:
        errors.append(f"Today has {today_blocks} scan blocks; cap is {max_today_blocks}.")

    for section_id, cap in section_caps.items():
        count = len(section_items(sections.get(section_id)))
        if count > cap:
            errors.append(f"{section_id} has {count} items; cap is {cap}.")

    for section in rendered_sections:
        section_id = section.get("id", "section")
        for index, item in enumerate(section_items(section)):
            label = item_label(section_id, index, item)
            verdict = str(item.get("verdict", "")).lower().strip()
            if verdict not in VERDICTS:
                errors.append(f"{label}: missing verdict act/watch/ignore.")
            body = str(item.get("body") or "").strip()
            if len(body) < 40 or not SO_WHAT.search(body):
                errors.append(f"{label}: body does not make a concrete so-what case.")
            if item.get("previously"):
                if WEAK_REPEAT.search(body):
                    errors.append(f"{label}: repeated item uses weak continuity language.")
                if not DELTA.search(body):
                    errors.append(f"{label}: repeated item needs a real delta.")

    for index, item in enumerate(hidden):
        label = item_label("hidden-signals", index, item)
        evidence = [entry for entry in item.get("evidence", []) if isinstance(entry, dict) and entry.get("url")]
        hosts = {host(entry.get("url", "")) for entry in evidence if host(entry.get("url", ""))}
        if len(evidence) < 2 or len(hosts) < 2:
            errors.append(f"{label}: hidden signal needs at least two independent evidence links.")
        body = str(item.get("body") or "")
        for phrase in ("Signal", "Evidence", "Why others miss it", "What to do"):
            if phrase.lower() not in body.lower():
                errors.append(f"{label}: body must include '{phrase}'.")

    for index, item in enumerate(section_items(sections.get("build-ideas"))):
        label = item_label("build-ideas", index, item)
        evidence = item.get("evidence")
        metrics = item.get("metrics")
        has_evidence_metric = any(
            isinstance(metric, dict) and str(metric.get("label", "")).lower() == "evidence"
            for metric in (metrics or [])
        )
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"{label}: build idea needs latest evidence.")
        if not has_evidence_metric:
            errors.append(f"{label}: build idea needs an evidence count metric.")

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a morning brief day file")
    parser.add_argument("--date", help="YYYY-MM-DD day to validate. Defaults to public/data/index.json latest.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        errors = validate(args.date)
    except Exception as error:
        print(f"validate_brief: {error}", file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Brief quality gate passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
