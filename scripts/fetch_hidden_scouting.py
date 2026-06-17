#!/usr/bin/env python3
"""Fetch raw scouting clues for hidden-signal synthesis.

These items are not rendered directly. They give the editorial agent earlier,
less obvious evidence than launch feeds: comments, issues, and watched page
changes that may reveal pain before a productized announcement exists.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import html
import json
import os
import re
import subprocess
import urllib.parse
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config.toml"
STATE_PATH = ROOT / "state" / "hidden_scouting_pages.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 morning-brief/1.0",
}

DEFAULTS = {
    "enabled": True,
    "max_items": 24,
    "lookback_hours": 72,
    "github_issue_queries": [
        "agent cost runaway",
        "stripe usage billing limits",
        "local llm benchmark mac",
        "claude code workflow blocked",
        "ai generated comments prompt leak",
    ],
    "github_issue_repos": [
        "anthropics/claude-code",
        "openai/openai-python",
        "vercel/ai",
        "huggingface/transformers",
        "ollama/ollama",
        "OpenHands/OpenHands",
        "langchain-ai/langchain",
        "browser-use/browser-use",
    ],
    "hn_comment_queries": [
        "AI created a problem",
        "agent costs",
        "Stripe event volume",
        "LLM local minima",
        "AI code review",
    ],
    "watch_pages": [
        "https://openai.com/api/pricing/",
        "https://docs.anthropic.com/en/docs/about-claude/models/overview",
        "https://vercel.com/docs/ai-sdk",
        "https://huggingface.co/models?sort=trending",
    ],
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
    section = config.get("sources", {}).get("hidden_scouting", {})
    if not isinstance(section, dict):
        return settings
    for key, default in DEFAULTS.items():
        value = section.get(key, default)
        if isinstance(value, type(default)):
            settings[key] = value
    return settings


def fetch(url: str, *, max_time: int = 30, extra_headers: dict[str, str] | None = None) -> str:
    args = [
        "curl",
        "--fail",
        "--location",
        "--silent",
        "--show-error",
        "--retry",
        "2",
        "--retry-all-errors",
        "--retry-delay",
        "1",
        "--retry-max-time",
        "30",
        "--max-time",
        str(max_time),
    ]
    headers = {**HEADERS, **(extra_headers or {})}
    for key, value in headers.items():
        args.extend(["--header", f"{key}: {value}"])
    args.append(url)
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        detail = result.stderr.strip().splitlines()
        raise RuntimeError(detail[-1] if detail else f"curl exited {result.returncode}")
    return result.stdout


def clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def trim(text: str, limit: int = 360) -> str:
    text = clean(text)
    if len(text) <= limit:
        return text
    cut = text[: limit - 1]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.rstrip(" ,;:.") + "…"


def hn_comments(query: str, cutoff: int) -> list[dict]:
    params = {
        "query": query,
        "tags": "comment",
        "numericFilters": f"created_at_i>{cutoff}",
        "hitsPerPage": "5",
    }
    payload = json.loads(fetch("https://hn.algolia.com/api/v1/search_by_date?" + urllib.parse.urlencode(params)))
    items = []
    for hit in payload.get("hits", []):
        comment_id = hit.get("objectID") or ""
        body = trim(hit.get("comment_text") or "")
        if not comment_id or len(body) < 80:
            continue
        points = hit.get("points")
        metrics = [{"label": "query", "value": query}]
        if isinstance(points, int) and points:
            metrics.append({"label": "points", "value": str(points)})
        items.append(
            {
                "type": "hn-comment",
                "source": "HN comments",
                "title": f"HN comment: {query}",
                "url": f"https://news.ycombinator.com/item?id={comment_id}",
                "body": body,
                "metrics": metrics,
            }
        )
    return items[:3]


def query_terms(query: str) -> list[str]:
    return [word.lower() for word in re.findall(r"[a-zA-Z0-9]+", query) if len(word) >= 4]


def matched_query(text: str, queries: list[str]) -> str | None:
    text = text.lower()
    best = None
    best_score = 0
    for query in queries:
        terms = query_terms(query)
        if not terms:
            continue
        score = sum(1 for term in terms if term in text)
        if score > best_score:
            best = query
            best_score = score
    return best if best_score >= 2 else None


def github_repo_issues(repo: str, queries: list[str], since_iso: str) -> list[dict]:
    url = f"https://api.github.com/repos/{repo}/issues?" + urllib.parse.urlencode(
        {"state": "all", "since": since_iso, "sort": "updated", "direction": "desc", "per_page": "25"}
    )
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    payload = json.loads(fetch(url, extra_headers=headers))
    items = []
    if not isinstance(payload, list):
        return items
    for issue in payload:
        if issue.get("pull_request"):
            continue
        body = trim(issue.get("body") or "")
        if not issue.get("html_url") or not issue.get("title"):
            continue
        match = matched_query(f"{issue.get('title') or ''} {body}", queries)
        if not match:
            continue
        metrics = [{"label": "repo", "value": repo}, {"label": "match", "value": match}]
        comments = issue.get("comments")
        if isinstance(comments, int) and comments:
            metrics.append({"label": "comments", "value": str(comments)})
        items.append(
            {
                "type": "github-issue",
                "source": "GitHub Issues",
                "title": clean(issue.get("title") or ""),
                "url": issue.get("html_url") or "",
                "body": body or "Issue title matched the hidden-scouting query.",
                "metrics": metrics,
            }
        )
    items.sort(
        key=lambda item: next(
            (int(metric["value"]) for metric in item["metrics"] if metric.get("label") == "comments" and str(metric.get("value", "")).isdigit()),
            0,
        ),
        reverse=True,
    )
    return items[:3]


def load_page_state() -> dict:
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"pages": {}}
    return data if isinstance(data, dict) else {"pages": {}}


def save_page_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def page_changes(urls: list[str]) -> tuple[list[dict], list[str]]:
    state = load_page_state()
    pages = state.setdefault("pages", {})
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    items: list[dict] = []
    notes: list[str] = []
    for url in urls:
        try:
            source = fetch(url, max_time=20)
        except Exception as error:
            notes.append(f"Watch page fetch failed ({url}): {error}")
            continue
        normalized = clean(source)
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        previous = pages.get(url, {})
        previous_digest = previous.get("sha256") if isinstance(previous, dict) else None
        pages[url] = {"sha256": digest, "checkedAt": now}
        if previous_digest and previous_digest != digest:
            items.append(
                {
                    "type": "watched-page-change",
                    "source": "Watched pages",
                    "title": f"Watched page changed: {urllib.parse.urlparse(url).netloc}",
                    "url": url,
                    "body": "A docs, pricing, or model page changed since the last run; inspect the diff before treating downstream launch posts as the first signal.",
                    "metrics": [{"label": "changed", "value": now[:10]}],
                }
            )
    save_page_state(state)
    return items, notes


def main() -> int:
    settings = load_settings()
    data = {"hidden_scouting": [], "access_notes": []}
    if not settings["enabled"]:
        data["access_notes"].append("Hidden scouting disabled in config.toml.")
        print(json.dumps(data, indent=2))
        return 0

    now = dt.datetime.now(dt.timezone.utc)
    cutoff = int((now - dt.timedelta(hours=settings["lookback_hours"])).timestamp())
    since_iso = (now - dt.timedelta(hours=settings["lookback_hours"])).isoformat()
    groups: list[list[dict]] = []

    for query in settings["hn_comment_queries"]:
        try:
            found = hn_comments(query, cutoff)
            if found:
                groups.append(found)
        except Exception as error:
            data["access_notes"].append(f"HN comment scouting failed ({query}): {error}")

    github_blocked = False
    for repo in settings["github_issue_repos"]:
        if github_blocked:
            break
        try:
            found = github_repo_issues(repo, settings["github_issue_queries"], since_iso)
            if found:
                groups.append(found)
        except Exception as error:
            message = str(error)
            if "403" in message:
                data["access_notes"].append(
                    "GitHub issue scouting blocked by API rate/auth limits; set GITHUB_TOKEN for this source."
                )
                github_blocked = True
            else:
                data["access_notes"].append(f"GitHub issue scouting failed ({repo}): {error}")

    try:
        changes, notes = page_changes(settings["watch_pages"])
        if changes:
            groups.append(changes)
        data["access_notes"].extend(notes)
    except Exception as error:
        data["access_notes"].append(f"Watched-page scouting failed: {error}")

    seen: set[str] = set()
    deduped = []
    max_items = int(settings["max_items"])
    while groups and len(deduped) < max_items:
        next_groups = []
        for group in groups:
            if not group:
                continue
            item = group.pop(0)
            key = item.get("url") or item.get("title")
            if key and key not in seen:
                seen.add(key)
                deduped.append(item)
                if len(deduped) >= max_items:
                    break
            if group:
                next_groups.append(group)
        groups = next_groups
    data["hidden_scouting"] = deduped
    print(json.dumps(data, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
