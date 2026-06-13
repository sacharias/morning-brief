#!/usr/bin/env python3
"""Fetch founder/opportunity signals with simple HTTP.

Demand signals (Ask HN + request-shaped Reddit posts), revenue proof
(Reddit + Show HN revenue milestones), and Product Hunt launches.
Follows the style of fetch_public_sources.py: curl via subprocess,
stdlib only, failures collected in access_notes, JSON to stdout.
"""

from __future__ import annotations

import datetime as dt
import html
import json
import os
import re
import subprocess
import time
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config.toml"
REDDIT_CACHE_PATH = ROOT / "state" / "reddit_public_cache.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 morning-brief/1.0",
}

# Reddit hard-blocks its .json API for unauthenticated/datacenter clients (HTTP
# 403), but still serves the public .rss feeds to ordinary browser requests.
# So we read top.rss with a real browser UA instead of top.json.
REDDIT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/atom+xml,application/xml,text/xml;q=0.9,*/*;q=0.8",
}

REDDIT_OAUTH_TOKEN: str | None = None

DEFAULTS = {
    "enabled": True,
    "subreddits": ["SaaS", "smallbusiness", "Entrepreneur", "SideProject", "LocalLLaMA", "indiehackers"],
    "lookback_hours": 72,
    "max_demand": 30,
    "max_revenue": 20,
    "max_launches": 25,
}

HN_REQUEST_QUERIES = [
    '"I\'d pay for"',
    '"is there a tool that"',
    '"looking for a tool"',
]

REQUEST_PATTERN = re.compile(
    r"\b(how do you|is there|i wish|looking for|alternative to|why is there no|"
    r"i'd pay|i would pay|struggling with|hate that|anyone know|any tool|"
    r"what do you use|recommend a|does anyone|need a tool|frustrated with)\b",
    re.I,
)

REVENUE_PATTERN = re.compile(
    r"\$\s?\d|\bMRR\b|\bARR\b|\bfirst customer\b|\bsold my\b|\bacquired\b|\brevenue\b",
    re.I,
)

REVENUE_SUBREDDITS = ["indiehackers", "SaaS", "SideProject"]
FOUNDER_SUBS = {"saas", "smallbusiness", "entrepreneur", "sideproject", "indiehackers"}
HIGH_ENGAGEMENT_SCORE = 150
BODY_LIMIT = 300
SUBREDDIT_HN_FALLBACK_QUERIES = {
    "smallbusiness": ["small business", "local business", "service business"],
    "localllama": ["local llm", "llama model", "open source llm"],
    "indiehackers": ["indie hacker", "bootstrapped", "mrr"],
}


def load_settings() -> dict:
    settings = dict(DEFAULTS)
    if tomllib is None or not CONFIG_PATH.exists():
        return settings
    try:
        with CONFIG_PATH.open("rb") as handle:
            config = tomllib.load(handle)
    except Exception:
        return settings
    section = config.get("sources", {}).get("founder_signals", {})
    if not isinstance(section, dict):
        return settings
    for key, default in DEFAULTS.items():
        value = section.get(key, default)
        if isinstance(value, type(default)):
            settings[key] = value
    return settings


def fetch(url: str, headers: dict[str, str] | None = None, method: str = "GET", data: dict[str, str] | None = None) -> str:
    args = [
        "curl",
        "--fail",
        "--location",
        "--silent",
        "--show-error",
        "--max-time",
        "30",
    ]
    if method != "GET":
        args.extend(["--request", method])
    if data:
        for key, value in data.items():
            args.extend(["--data-urlencode", f"{key}={value}"])
    for key, value in (headers or HEADERS).items():
        args.extend(["--header", f"{key}: {value}"])
    args.append(url)
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        detail = result.stderr.strip().splitlines()
        raise RuntimeError(detail[-1] if detail else f"curl exited {result.returncode}")
    return result.stdout


def fetch_with_retries(url: str, headers: dict[str, str] | None = None, attempts: int = 3) -> str:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            return fetch(url, headers=headers)
        except Exception as error:
            last_error = error
            if attempt + 1 < attempts:
                time.sleep(1.5 * (attempt + 1))
    raise last_error or RuntimeError("request did not run")


def clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def trim_body(text: str) -> str:
    text = clean(text or "")
    if len(text) <= BODY_LIMIT:
        return text
    cut = text[: BODY_LIMIT - 1]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut + "…"


def normalize_title(title: str) -> str:
    return clean(title).replace("’", "'").replace("“", '"').replace("”", '"')


def make_item(title: str, url: str, body: str, source: str, points=None, comments=None) -> dict:
    item = {
        "title": normalize_title(title),
        "url": url,
        "body": trim_body(body),
        "source": source,
    }
    if points is not None:
        item["points"] = int(points)
    if comments is not None:
        item["comments"] = int(comments)
    return item


def engagement(item: dict) -> int:
    return int(item.get("points") or 0) + int(item.get("comments") or 0)


def rank_and_trim(items: list[dict], limit: int) -> list[dict]:
    """Sort by engagement (Reddit items, which lack scores, fall back to their
    position in the top feed), drop the internal sort hint, and cap the list."""
    items.sort(key=lambda it: it.get("_sort", engagement(it)), reverse=True)
    for item in items:
        item.pop("_sort", None)
    return items[:limit]


def hn_search(params: dict[str, str]) -> list[dict]:
    url = "https://hn.algolia.com/api/v1/search_by_date?" + urllib.parse.urlencode(params)
    payload = json.loads(fetch(url))
    return payload.get("hits", [])


def reddit_oauth_token() -> str | None:
    global REDDIT_OAUTH_TOKEN
    if REDDIT_OAUTH_TOKEN:
        return REDDIT_OAUTH_TOKEN
    client_id = os.environ.get("REDDIT_CLIENT_ID")
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
    if not client_id or not client_secret:
        return None
    auth = subprocess.run(
        [
            "curl",
            "--fail",
            "--silent",
            "--show-error",
            "--max-time",
            "30",
            "--user",
            f"{client_id}:{client_secret}",
            "--header",
            "User-Agent: morning-brief/1.0",
            "--data",
            "grant_type=client_credentials",
            "https://www.reddit.com/api/v1/access_token",
        ],
        capture_output=True,
        text=True,
    )
    if auth.returncode != 0:
        return None
    try:
        token = json.loads(auth.stdout).get("access_token")
    except json.JSONDecodeError:
        token = None
    REDDIT_OAUTH_TOKEN = token if isinstance(token, str) and token else None
    return REDDIT_OAUTH_TOKEN


def parse_reddit_json(payload: str, subreddit: str) -> list[dict]:
    data = json.loads(payload)
    posts: list[dict] = []
    for rank, child in enumerate(data.get("data", {}).get("children", [])):
        post = child.get("data", {}) if isinstance(child, dict) else {}
        permalink = post.get("permalink") or ""
        url = permalink if permalink.startswith("http") else f"https://www.reddit.com{permalink}"
        posts.append(
            {
                "title": post.get("title") or "",
                "permalink_url": url,
                "selftext": post.get("selftext") or "",
                "subreddit": post.get("subreddit") or subreddit,
                "created_utc": float(post.get("created_utc") or 0),
                "score": int(post.get("score") or 0),
                "num_comments": int(post.get("num_comments") or 0),
                "_feedrank": 100 - rank,
            }
        )
    return posts


def reddit_top_oauth(subreddit: str) -> list[dict]:
    token = reddit_oauth_token()
    if not token:
        return []
    url = f"https://oauth.reddit.com/r/{subreddit}/top.json?t=day&limit=50"
    return parse_reddit_json(
        fetch(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "User-Agent": "morning-brief/1.0",
                "Accept": "application/json",
            },
        ),
        subreddit,
    )


def load_reddit_cache() -> dict[str, list[dict]]:
    try:
        data = json.loads(REDDIT_CACHE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    cached = data.get("subreddits", {}) if isinstance(data, dict) else {}
    return cached if isinstance(cached, dict) else {}


def save_reddit_cache(cache: dict[str, list[dict]]) -> None:
    try:
        REDDIT_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        REDDIT_CACHE_PATH.write_text(
            json.dumps({"updated_at": dt.datetime.now(dt.timezone.utc).isoformat(), "subreddits": cache}, indent=2)
            + "\n",
            encoding="utf-8",
        )
    except OSError:
        pass


def hn_item(hit: dict, source: str) -> dict:
    object_id = hit.get("objectID", "")
    url = hit.get("url") or f"https://news.ycombinator.com/item?id={object_id}"
    return make_item(
        hit.get("title") or "",
        url,
        hit.get("story_text") or "",
        source,
        points=hit.get("points") or 0,
        comments=hit.get("num_comments") or 0,
    )


def hn_fallback_posts(subreddit: str, lookback_hours: int = 72) -> list[dict]:
    key = subreddit.lower()
    queries = SUBREDDIT_HN_FALLBACK_QUERIES.get(key, [subreddit])
    cutoff = int(dt.datetime.now(dt.timezone.utc).timestamp()) - lookback_hours * 3600
    posts: list[dict] = []
    seen: set[str] = set()
    for query in queries:
        for hit in hn_search(
            {
                "query": query,
                "tags": "story",
                "numericFilters": f"created_at_i>{cutoff},points>=2",
                "hitsPerPage": "30",
            }
        ):
            object_id = hit.get("objectID", "")
            url = hit.get("url") or f"https://news.ycombinator.com/item?id={object_id}"
            title = hit.get("title") or ""
            if not url or url in seen or not title:
                continue
            seen.add(url)
            posts.append(
                {
                    "title": title,
                    "permalink_url": url,
                    "selftext": hit.get("story_text") or "",
                    "subreddit": subreddit,
                    "source_label": f"HN fallback for r/{subreddit}",
                    "created_utc": float(hit.get("created_at_i") or 0),
                    "score": int(hit.get("points") or 0),
                    "num_comments": int(hit.get("num_comments") or 0),
                    "_feedrank": int(hit.get("points") or 0) + int(hit.get("num_comments") or 0),
                }
            )
    return posts


# Reddit's RSS content wraps the selftext in a navigation table; drop the
# "submitted by /u/… [link] [comments]" footer it appends.
REDDIT_FOOTER = re.compile(r"\s*submitted by\b.*$", re.I | re.S)


def parse_reddit_rss(source: str, subreddit: str) -> list[dict]:
    """Parse a Reddit top.rss Atom feed into post data dicts shaped like the
    fields the rest of this module expects (title/permalink/selftext/…)."""
    ns = {"a": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(source)
    posts: list[dict] = []
    for rank, entry in enumerate(root.findall("a:entry", ns)):
        link_el = entry.find("a:link", ns)
        permalink = link_el.get("href") if link_el is not None else ""
        if not permalink:
            continue
        content = entry.findtext("a:content", default="", namespaces=ns) or ""
        body = REDDIT_FOOTER.sub("", clean(content))
        published = entry.findtext("a:published", default="", namespaces=ns) or entry.findtext(
            "a:updated", default="", namespaces=ns
        )
        try:
            created = dt.datetime.fromisoformat(published).timestamp() if published else 0
        except ValueError:
            created = 0
        posts.append(
            {
                "title": entry.findtext("a:title", default="", namespaces=ns) or "",
                "permalink_url": permalink,
                "selftext": body,
                "subreddit": subreddit,
                "created_utc": created,
                # RSS carries no score; rank within the (already top-sorted) feed
                # stands in for ordering only — never surfaced as a fake metric.
                "_feedrank": 100 - rank,
            }
        )
    return posts


def reddit_top_of_day(subreddit: str, cache: dict[str, list[dict]], notes: list[str]) -> list[dict]:
    """Return top-of-day post data dicts for a subreddit, caching per run."""
    key = subreddit.lower()
    if key in cache:
        return cache[key]
    stored_cache = load_reddit_cache()

    try:
        posts = reddit_top_oauth(subreddit)
        if posts:
            cache[key] = posts
            stored_cache[key] = posts
            save_reddit_cache(stored_cache)
            return posts
    except Exception:
        pass

    posts: list[dict] = []
    last_error: Exception | None = None
    for host in ("www.reddit.com", "old.reddit.com"):
        try:
            source = fetch_with_retries(
                f"https://{host}/r/{subreddit}/top.rss?t=day&limit=50", headers=REDDIT_HEADERS
            )
            posts = parse_reddit_rss(source, subreddit)
            last_error = None
            break
        except Exception as error:
            last_error = error
    if last_error is not None:
        cached = stored_cache.get(key)
        if isinstance(cached, list) and cached:
            cache[key] = cached
            return cached
        try:
            posts = hn_fallback_posts(subreddit)
            if posts:
                cache[key] = posts
                return posts
        except Exception:
            pass
        notes.append(f"Reddit r/{subreddit} has no live public fallback available; set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET for official API access.")
    cache[key] = posts
    if posts:
        stored_cache[key] = posts
        save_reddit_cache(stored_cache)
    return posts


def reddit_item(data: dict) -> dict:
    subreddit = data.get("subreddit") or ""
    item = make_item(
        data.get("title") or "",
        data.get("permalink_url") or "",
        data.get("selftext") or "",
        data.get("source_label") or f"r/{subreddit}",
        # RSS exposes no score/comment counts, so leave the metrics off rather
        # than render a misleading zero.
        points=data.get("score"),
        comments=data.get("num_comments"),
    )
    if data.get("_feedrank") is not None:
        item["_sort"] = data["_feedrank"]
    return item


def demand_signals(settings: dict, cache: dict[str, list[dict]], notes: list[str]) -> list[dict]:
    cutoff = int(dt.datetime.now(dt.timezone.utc).timestamp()) - settings["lookback_hours"] * 3600
    items: list[dict] = []
    seen: set[str] = set()

    def add(item: dict) -> None:
        if item["url"] and item["url"] not in seen and item["title"]:
            seen.add(item["url"])
            items.append(item)

    searches = [({"tags": "ask_hn", "numericFilters": f"created_at_i>{cutoff},points>=3", "hitsPerPage": "100"}, "Ask HN")]
    for query in HN_REQUEST_QUERIES:
        searches.append(
            (
                {
                    "query": query,
                    "tags": "story",
                    "numericFilters": f"created_at_i>{cutoff},points>=2",
                    "hitsPerPage": "50",
                },
                "Hacker News",
            )
        )
    for params, source in searches:
        try:
            for hit in hn_search(params):
                if not hit.get("title"):
                    continue
                title = normalize_title(hit["title"])
                if source == "Ask HN" and not (
                    REQUEST_PATTERN.search(title) or (hit.get("points") or 0) >= 10
                ):
                    continue
                add(hn_item(hit, source))
        except Exception as error:
            label = params.get("query") or params.get("tags", "search")
            notes.append(f"HN Algolia demand search ({label}) failed: {error}")

    for subreddit in settings["subreddits"]:
        for data in reddit_top_of_day(subreddit, cache, notes):
            if (data.get("created_utc") or 0) < cutoff:
                continue
            title = normalize_title(data.get("title") or "")
            request_shaped = bool(REQUEST_PATTERN.search(title))
            high_engagement = (
                (data.get("subreddit") or "").lower() in FOUNDER_SUBS
                and (data.get("score") or 0) >= HIGH_ENGAGEMENT_SCORE
            )
            if request_shaped or high_engagement:
                add(reddit_item(data))

    return rank_and_trim(items, settings["max_demand"])


def revenue_proof(settings: dict, cache: dict[str, list[dict]], notes: list[str]) -> list[dict]:
    cutoff = int(dt.datetime.now(dt.timezone.utc).timestamp()) - settings["lookback_hours"] * 3600
    items: list[dict] = []
    seen: set[str] = set()

    def add(item: dict) -> None:
        if item["url"] and item["url"] not in seen and item["title"]:
            seen.add(item["url"])
            items.append(item)

    for subreddit in REVENUE_SUBREDDITS:
        for data in reddit_top_of_day(subreddit, cache, notes):
            if (data.get("created_utc") or 0) < cutoff:
                continue
            haystack = f"{data.get('title') or ''} {data.get('selftext') or ''}"
            if REVENUE_PATTERN.search(haystack):
                add(reddit_item(data))

    for query in ('"Show HN" MRR', '"Show HN" revenue'):
        try:
            hits = hn_search(
                {
                    "query": query,
                    "tags": "show_hn",
                    "numericFilters": f"created_at_i>{cutoff}",
                    "hitsPerPage": "50",
                }
            )
            for hit in hits:
                haystack = f"{hit.get('title') or ''} {hit.get('story_text') or ''}"
                if hit.get("title") and REVENUE_PATTERN.search(haystack):
                    add(hn_item(hit, "Show HN"))
        except Exception as error:
            notes.append(f"HN Algolia revenue search ({query}) failed: {error}")

    return rank_and_trim(items, settings["max_revenue"])


def parse_atom_entries(source: str) -> list[dict]:
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    entries = []
    root = ET.fromstring(source)
    for entry in root.findall("atom:entry", ns):
        title = entry.findtext("atom:title", default="", namespaces=ns)
        link = ""
        for link_el in entry.findall("atom:link", ns):
            if link_el.get("rel") in (None, "alternate"):
                link = link_el.get("href") or ""
                break
        body = entry.findtext("atom:content", default="", namespaces=ns) or entry.findtext(
            "atom:summary", default="", namespaces=ns
        )
        entries.append({"title": title, "url": link, "body": body})
    return entries


def parse_atom_entries_regex(source: str) -> list[dict]:
    entries = []
    for block in re.findall(r"<entry\b[\s\S]*?</entry>", source):
        title_match = re.search(r"<title[^>]*>([\s\S]*?)</title>", block)
        link_match = re.search(r'<link\b[^>]*href="([^"]+)"', block)
        body_match = re.search(r"<(?:content|summary)\b[^>]*>([\s\S]*?)</(?:content|summary)>", block)
        if not title_match or not link_match:
            continue
        entries.append(
            {
                "title": title_match.group(1),
                "url": link_match.group(1),
                "body": body_match.group(1) if body_match else "",
            }
        )
    return entries


def launches(settings: dict, notes: list[str]) -> list[dict]:
    try:
        source = fetch("https://www.producthunt.com/feed")
    except Exception as error:
        notes.append(f"Product Hunt feed fetch failed (likely blocked): {error}")
        return []
    try:
        entries = parse_atom_entries(source)
    except Exception:
        entries = parse_atom_entries_regex(source)
    if not entries:
        notes.append("Product Hunt feed returned no parseable entries.")
        return []
    items = []
    seen: set[str] = set()
    for entry in entries:
        url = entry["url"]
        if not url or url in seen or not clean(entry["title"]):
            continue
        seen.add(url)
        items.append(make_item(entry["title"], url, entry["body"], "Product Hunt"))
    return items[: settings["max_launches"]]


def main() -> int:
    settings = load_settings()
    data = {
        "demand_signals": [],
        "revenue_proof": [],
        "launches": [],
        "access_notes": [],
    }
    notes: list[str] = data["access_notes"]
    if not settings["enabled"]:
        notes.append("Founder signals disabled in config.toml.")
        print(json.dumps(data, indent=2))
        return 0
    reddit_cache: dict[str, list[dict]] = {}
    try:
        data["demand_signals"] = demand_signals(settings, reddit_cache, notes)
    except Exception as error:
        notes.append(f"Demand signals failed: {error}")
    try:
        data["revenue_proof"] = revenue_proof(settings, reddit_cache, notes)
    except Exception as error:
        notes.append(f"Revenue proof failed: {error}")
    try:
        data["launches"] = launches(settings, notes)
    except Exception as error:
        notes.append(f"Product Hunt launches failed: {error}")
    required = {
        "demand_signals": "Demand signals",
        "revenue_proof": "Revenue proof",
        "launches": "Launches",
    }
    for key, label in required.items():
        if not data[key]:
            notes.append(f"{label} returned no usable public-source items.")
    print(json.dumps(data, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
