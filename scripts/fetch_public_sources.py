#!/usr/bin/env python3
"""Fetch public morning-brief sources with simple HTTP.

This intentionally avoids browser automation. Use it for GitHub Trending and
Hugging Face Papers before escalating to Playwright or Chrome.
"""

from __future__ import annotations

import html
import json
import re
import subprocess


HEADERS = {
    "User-Agent": "Mozilla/5.0 morning-brief/1.0",
}


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


def clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def github_trending(limit: int = 10) -> list[dict[str, str]]:
    source = fetch("https://github.com/trending?since=daily")
    rows = re.findall(r'<article\b[^>]*class="[^"]*Box-row[^"]*"[\s\S]*?</article>', source)
    items = []
    for row in rows[:limit]:
        repo_match = re.search(r'<h2[\s\S]*?<a\b[^>]*href="/([^"]+)"[\s\S]*?</a>', row)
        if not repo_match:
            continue
        repo = clean(repo_match.group(1))
        desc_match = re.search(r"<p\b[^>]*>([\s\S]*?)</p>", row)
        lang_match = re.search(r'itemprop="programmingLanguage"[^>]*>(.*?)</span>', row)
        stars_today_match = re.search(r"([\d,]+\s+stars today)", clean(row), re.I)
        items.append(
            {
                "repo": repo,
                "url": f"https://github.com/{repo}",
                "description": clean(desc_match.group(1)) if desc_match else "",
                "language": clean(lang_match.group(1)) if lang_match else "",
                "stars_today": stars_today_match.group(1) if stars_today_match else "",
            }
        )
    return items


def huggingface_papers(limit: int = 10) -> list[dict[str, str]]:
    source = fetch("https://huggingface.co/papers")
    matches = re.finditer(r'href="/papers/(\d+\.\d+)"[^>]*>([\s\S]*?)</a>', source)
    seen: set[str] = set()
    items = []
    for match in matches:
        paper_id = match.group(1)
        title = clean(match.group(2))
        if paper_id in seen or not title or title.isdigit() or title.startswith("·"):
            continue
        seen.add(paper_id)
        items.append(
            {
                "id": paper_id,
                "title": title,
                "url": f"https://huggingface.co/papers/{paper_id}",
            }
        )
        if len(items) >= limit:
            break
    return items


def main() -> int:
    data = {
        "github_trending": github_trending(),
        "huggingface_papers": huggingface_papers(),
    }
    print(json.dumps(data, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
