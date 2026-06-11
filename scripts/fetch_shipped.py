#!/usr/bin/env python3
"""Fetch "Shipped" items: vendor release feeds, HF trending models, GitHub releases.

Stdlib only, curl via subprocess (same pattern as fetch_public_sources.py).
Prints {"shipped": [...], "access_notes": [...]} to stdout and always exits 0.
"""

from __future__ import annotations

import datetime as dt
import email.utils
import html
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config.toml"

HEADERS = {
    "User-Agent": "Mozilla/5.0 morning-brief/1.0",
}

# Verified 2026-06-11. The official Anthropic feed (anthropic.com/news/rss.xml)
# and Meta AI feed (ai.meta.com/blog/rss/) both return 404, so Anthropic uses an
# RSSHub mirror and Meta uses the Meta Engineering AI-research category feed.
DEFAULT_FEEDS = [
    {"name": "OpenAI", "url": "https://openai.com/news/rss.xml"},
    {"name": "Anthropic", "url": "https://rsshub.rssforever.com/anthropic/news"},
    {"name": "Google AI", "url": "https://blog.google/technology/ai/rss/"},
    {"name": "Meta AI", "url": "https://engineering.fb.com/category/ai-research/feed/"},
    {"name": "Hugging Face", "url": "https://huggingface.co/blog/feed.xml"},
    {"name": "DeepMind", "url": "https://deepmind.google/blog/rss.xml"},
]

DEFAULT_PINNED_REPOS = [
    "anthropics/anthropic-sdk-python",
    "anthropics/claude-code",
    "openai/openai-python",
    "vercel/ai",
    "huggingface/transformers",
    "ollama/ollama",
]

DEFAULT_LOOKBACK_HOURS = 72
DEFAULT_MAX_ITEMS = 40

HF_MODELS_URL = "https://huggingface.co/api/models?sort=trendingScore&direction=-1&limit=25"


def fetch(url: str) -> str:
    args = [
        "curl",
        "--fail",
        "--location",
        "--silent",
        "--show-error",
        "--max-time",
        "30",
    ]
    for key, value in HEADERS.items():
        args.extend(["--header", f"{key}: {value}"])
    args.append(url)
    result = subprocess.run(args, check=True, capture_output=True, text=True)
    return result.stdout


def load_shipped_config() -> dict:
    if not CONFIG_PATH.exists() or tomllib is None:
        return {}
    try:
        with CONFIG_PATH.open("rb") as handle:
            config = tomllib.load(handle)
    except Exception:
        return {}
    shipped = config.get("sources", {}).get("shipped", {})
    return shipped if isinstance(shipped, dict) else {}


def clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def trim_body(text: str, limit: int = 300) -> str:
    text = clean(text)
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0]
    return cut.rstrip(" ,;:.") + "…"


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def child_text(element: ET.Element, *names: str) -> str:
    wanted = set(names)
    for child in element:
        if local_name(child.tag) in wanted and child.text:
            return child.text
    return ""


def entry_link(element: ET.Element) -> str:
    fallback = ""
    for child in element:
        name = local_name(child.tag)
        if name == "link":
            href = child.get("href")
            if href:
                if child.get("rel") in (None, "alternate"):
                    return href.strip()
                fallback = fallback or href.strip()
            elif child.text and child.text.strip():
                return child.text.strip()
    return fallback


def parse_date(value: str) -> dt.datetime | None:
    value = (value or "").strip()
    if not value:
        return None
    parsed = None
    try:
        parsed = email.utils.parsedate_to_datetime(value)
    except (TypeError, ValueError):
        try:
            parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def parse_feed_entries(source: str) -> list[dict]:
    """Parse RSS 2.0 or Atom into raw entries: {title, url, body, published}."""
    root = ET.fromstring(source)
    if local_name(root.tag) == "feed":
        elements = [child for child in root if local_name(child.tag) == "entry"]
    else:
        elements = [
            item
            for channel in root
            if local_name(channel.tag) == "channel"
            for item in channel
            if local_name(item.tag) == "item"
        ]
    entries = []
    for element in elements:
        entries.append(
            {
                "title": clean(child_text(element, "title")),
                "url": entry_link(element) or child_text(element, "guid", "id").strip(),
                "body": child_text(element, "description", "summary", "content", "encoded"),
                "published": parse_date(
                    child_text(element, "pubDate", "published", "updated", "date")
                ),
            }
        )
    return entries


def feed_items(name: str, url: str, cutoff: dt.datetime) -> list[dict]:
    items = []
    for entry in parse_feed_entries(fetch(url)):
        published = entry["published"]
        if not entry["title"] or published is None or published < cutoff:
            continue
        items.append(
            {
                "title": entry["title"],
                "url": entry["url"],
                "body": trim_body(entry["body"]),
                "source": name,
                "published": published.isoformat(),
            }
        )
    return items


def release_items(repo: str, cutoff: dt.datetime) -> list[dict]:
    items = []
    for entry in parse_feed_entries(fetch(f"https://github.com/{repo}/releases.atom")):
        published = entry["published"]
        if not entry["title"] or published is None or published < cutoff:
            continue
        items.append(
            {
                "title": f"{repo} {entry['title']}",
                "url": entry["url"],
                "body": trim_body(entry["body"]),
                "source": "GitHub Releases",
                "published": published.isoformat(),
            }
        )
    return items


def trending_model_items() -> list[dict]:
    models = json.loads(fetch(HF_MODELS_URL))
    items = []
    for model in models:
        model_id = model.get("id") or model.get("modelId")
        if not model_id:
            continue
        parts = []
        if model.get("pipeline_tag"):
            parts.append(str(model["pipeline_tag"]))
        if model.get("likes") is not None:
            parts.append(f"{model['likes']:,} likes")
        if model.get("downloads") is not None:
            parts.append(f"{model['downloads']:,} downloads")
        items.append(
            {
                "title": model_id,
                "url": f"https://huggingface.co/{model_id}",
                "body": "Trending on Hugging Face: " + " · ".join(parts) + "."
                if parts
                else "Trending on Hugging Face.",
                "source": "HF Models",
                "published": None,
            }
        )
    return items


def main() -> int:
    data = {"shipped": [], "access_notes": []}
    try:
        config = load_shipped_config()
        if not config.get("enabled", True):
            data["access_notes"].append("Shipped sources disabled in config.")
            print(json.dumps(data, indent=2))
            return 0

        lookback_hours = config.get("lookback_hours", DEFAULT_LOOKBACK_HOURS)
        max_items = config.get("max_items", DEFAULT_MAX_ITEMS)
        feeds = [
            feed
            for feed in (config.get("feeds") or DEFAULT_FEEDS)
            if isinstance(feed, dict) and feed.get("name") and feed.get("url")
        ]
        repos = [repo for repo in (config.get("pinned_repos") or DEFAULT_PINNED_REPOS) if isinstance(repo, str)]
        cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=lookback_hours)

        tasks = [
            (f"Feed {feed['name']}", lambda feed=feed: feed_items(feed["name"], feed["url"], cutoff))
            for feed in feeds
        ]
        tasks.append(("HF trending models", trending_model_items))
        tasks += [
            (f"GitHub releases {repo}", lambda repo=repo: release_items(repo, cutoff))
            for repo in repos
        ]

        def run_task(task):
            label, func = task
            try:
                return func(), None
            except Exception as error:
                return [], f"{label} fetch failed: {error}"

        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(run_task, tasks))

        dated, undated = [], []
        for items, note in results:
            if note:
                data["access_notes"].append(note)
            for item in items:
                (dated if item["published"] else undated).append(item)
        dated.sort(key=lambda item: item["published"], reverse=True)
        data["shipped"] = (dated + undated)[:max_items]
    except Exception as error:
        data["access_notes"].append(f"Shipped fetch failed: {error}")
    print(json.dumps(data, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
