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


def clean_markdown(text: str) -> str:
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\[\[\d+\][^\]]*\]", " ", text)
    text = re.sub(r"#+\s*", " ", text)
    text = re.sub(r"[_*`$]+", "", text)
    text = text.replace("\\", "")
    return clean(text)


def split_sentences(text: str) -> list[str]:
    text = clean_markdown(text)
    if not text:
        return []
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", text)
    return [sentence.strip() for sentence in sentences if sentence.strip()]


def abstract_from_markdown(markdown: str) -> str:
    lines = markdown.splitlines()
    abstract_lines = [
        index
        for index, line in enumerate(lines)
        if re.sub(r"^#{1,6}\s*", "", line.strip()).lower() == "abstract"
    ]
    for index in reversed(abstract_lines):
        block = []
        for line in lines[index + 1 :]:
            stripped = line.strip()
            normalized = re.sub(r"^#{1,6}\s*", "", stripped)
            if block and re.match(r"^(?:\d+(?:\.\d+)?)?\s*(Introduction|Related Work|References)\b", normalized, re.I):
                break
            block.append(line)
        text = clean_markdown("\n".join(block))
        if len(text) >= 80 and not re.match(r"^\d+\s*Introduction\b", text, re.I):
            return text
    return ""


def introduction_from_markdown(markdown: str) -> str:
    match = re.search(r"(?:^|\n)(?:#{1,6}\s*)?(?:\d+(?:\.\d+)?)?\s*Introduction\s*\n(?P<intro>[\s\S]*?)(?:\n(?:#{1,6}\s*)?(?:\d+(?:\.\d+)?)?\s*[A-Z][^\n]{0,80}\n|\Z)", markdown, re.I)
    if match:
        return clean_markdown(match.group("intro"))
    return ""


def choose_summary(sentences: list[str]) -> str:
    if not sentences:
        return ""
    topic_pattern = re.compile(
        r"\b(we introduce|we present|we propose|we examine|we characterize|we study|we analyze|"
        r"we develop|this paper|to address|our study)\b",
        re.I,
    )
    result_pattern = re.compile(r"\b(show|find|reveal|achiev|evaluate|covers|compris|demonstrat|result|provides)\b", re.I)

    first_index = next((idx for idx, sentence in enumerate(sentences) if topic_pattern.search(sentence)), 0)
    selected = [sentences[first_index]]

    second = next(
        (
            sentence
            for idx, sentence in enumerate(sentences[first_index + 1 :], start=first_index + 1)
            if result_pattern.search(sentence)
        ),
        None,
    )
    if second is None:
        second = next((sentence for sentence in sentences[first_index + 1 :] if sentence not in selected), None)
    if second is None and first_index > 0:
        second = sentences[0]
    if second is None:
        second = "Open the paper for the method and results."
    selected.append(second)
    return " ".join(selected[:2])


def paper_summary(paper_id: str, title: str) -> str:
    try:
        markdown = fetch(f"https://huggingface.co/papers/{paper_id}.md")
    except Exception:
        return f"This paper is about {title}. Open the paper for the abstract, method, and results."

    sentences = split_sentences(abstract_from_markdown(markdown)) or split_sentences(introduction_from_markdown(markdown))
    summary = choose_summary(sentences)
    if summary:
        return summary
    return f"This paper is about {title}. Open the paper for the abstract, method, and results."


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
                "summary": paper_summary(paper_id, title),
            }
        )
        if len(items) >= limit:
            break
    return items


def main() -> int:
    data = {
        "github_trending": [],
        "huggingface_papers": [],
        "access_notes": [],
    }
    try:
        data["github_trending"] = github_trending()
    except Exception as error:
        data["access_notes"].append(f"GitHub Trending fetch failed: {error}")
    try:
        data["huggingface_papers"] = huggingface_papers()
    except Exception as error:
        data["access_notes"].append(f"Hugging Face Papers fetch failed: {error}")
    print(json.dumps(data, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
