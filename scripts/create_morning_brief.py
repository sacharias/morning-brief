#!/usr/bin/env python3
"""Create a dated morning brief report."""

from __future__ import annotations

import argparse
import datetime as dt
import html as html_lib
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


def run_json_safe(command: list[str], timeout: int, fallback: dict, label: str) -> dict:
    try:
        return run_json(command, timeout=timeout)
    except Exception as error:
        data = dict(fallback)
        notes = list(data.get("access_notes", []))
        notes.append(f"{label} failed: {error}")
        data["access_notes"] = notes
        return data


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
    return ", ".join(parts) if parts else "metrics unavailable"


def tweet_line(item: dict) -> str:
    author = item.get("author_screen_name") or item.get("author_name") or "x"
    text = truncate(item.get("text", ""))
    return f"- [@{author}]({item.get('url', '')}) - {text}\n  - {metric_summary(item)}"


def github_line(item: dict) -> str:
    desc = truncate(item.get("description", ""), 180)
    meta = ", ".join(part for part in (item.get("language"), item.get("stars_today")) if part)
    suffix = f" ({meta})" if meta else ""
    return f"- [{item.get('repo')}]({item.get('url')}){suffix} - {desc}"


def paper_line(item: dict) -> str:
    summary = paper_summary_text(item)
    return f"- [{item.get('title')}]({item.get('url')})\n  - {summary}"


def fmt_number(value: object) -> str:
    if isinstance(value, int):
        return f"{value:,}"
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return "0"


def escape(value: object) -> str:
    return html_lib.escape(str(value or ""), quote=True)


def item_url(item: dict) -> str:
    return escape(item.get("url", "#"))


def metric_chips(item: dict) -> str:
    metrics = [
        ("Likes", "favorite_count"),
        ("Reposts", "retweet_count"),
        ("Replies", "reply_count"),
        ("Quotes", "quote_count"),
        ("Bookmarks", "bookmark_count"),
    ]
    chips = []
    for label, key in metrics:
        value = item.get(key)
        if isinstance(value, int) and value:
            chips.append(f"<span><strong>{fmt_number(value)}</strong>{label}</span>")
    return "".join(chips) if chips else "<span>Metrics unavailable</span>"


def tweet_card(item: dict, index: int) -> str:
    author = item.get("author_screen_name") or item.get("author_name") or "x"
    author_label = f"@{author}"
    full_text = re.sub(r"\s+", " ", item.get("text", "")).strip()
    preview = truncate(full_text, 260)
    details = ""
    if full_text and preview != full_text:
        details = f"""
            <details class="item-details">
              <summary>Full text</summary>
              <div class="detail-copy">
                <p>{escape(full_text)}</p>
              </div>
            </details>"""
    return f"""
          <article class="item-card tweet-card">
            <div class="item-top">
              <span class="item-rank">{index:02d}</span>
              <a class="item-title" href="{item_url(item)}" target="_blank" rel="noreferrer">{escape(author_label)}</a>
            </div>
            <p class="item-text">{escape(preview or "No text captured.")}</p>
            <div class="metric-row">{metric_chips(item)}</div>
{details}
          </article>"""


def github_card(item: dict, index: int) -> str:
    full_desc = re.sub(r"\s+", " ", item.get("description", "")).strip()
    desc = truncate(full_desc, 260)
    meta = [part for part in (item.get("language"), item.get("stars_today")) if part]
    meta_html = "".join(f"<span>{escape(part)}</span>" for part in meta)
    details = ""
    if full_desc and desc != full_desc:
        details = f"""
            <details class="item-details">
              <summary>Full description</summary>
              <div class="detail-copy">
                <p>{escape(full_desc)}</p>
              </div>
            </details>"""
    return f"""
          <article class="item-card project-card">
            <div class="item-top">
              <span class="item-rank">{index:02d}</span>
              <a class="item-title" href="{item_url(item)}" target="_blank" rel="noreferrer">{escape(item.get("repo", "repository"))}</a>
            </div>
            <p class="item-text">{escape(desc)}</p>
            <div class="metric-row">{meta_html or "<span>Repository metadata unavailable</span>"}</div>
{details}
          </article>"""


def paper_summary_text(item: dict) -> str:
    title = item.get("title", "this paper")
    summary = re.sub(r"\s+", " ", item.get("summary", "")).strip()
    if summary:
        return summary
    return f"This paper is about {title}. Open the paper for the abstract, method, and results."


def paper_card(item: dict, index: int) -> str:
    summary = paper_summary_text(item)
    return f"""
          <article class="item-card paper-card">
            <div class="item-top">
              <span class="item-rank">{index:02d}</span>
              <a class="item-title" href="{item_url(item)}" target="_blank" rel="noreferrer">{escape(item.get("title", "Untitled paper"))}</a>
            </div>
            <p class="item-text">{escape(summary)}</p>
          </article>"""


def render_cards(items: list[dict], renderer, empty: str) -> str:
    if not items:
        return f'<p class="empty-state">{escape(empty)}</p>'
    return "\n".join(renderer(item, index) for index, item in enumerate(items, start=1))


def run_note_section(public_notes: list[str], x_notes: list[str]) -> str:
    notes = []
    for note in public_notes:
        notes.append(f"<li>{escape(note)}</li>")
    for note in x_notes:
        notes.append(f"<li>{escape(note)}</li>")
    if not notes:
        return ""
    note_items = "\n".join(notes)
    return f"""
    <section class="section">
      <div class="section-head">
        <h2>Run Notes</h2>
      </div>
      <ul class="run-notes">
{note_items}
      </ul>
    </section>"""


def build_html(public: dict, x_data: dict, config: dict, generated_at: dt.datetime) -> str:
    output_cfg = config.get("output", {})
    top_github = int(output_cfg.get("top_github_projects", 5))
    top_papers = int(output_cfg.get("top_huggingface_papers", 5))

    bookmarks = x_data.get("x_bookmarks", [])
    top_posts = x_data.get("top_x_posts", [])
    github = public.get("github_trending", [])[:top_github]
    papers = public.get("huggingface_papers", [])[:top_papers]
    public_notes = public.get("access_notes", [])
    x_notes = x_data.get("access_notes", [])
    title = config.get("brief_title", "Morning Brief")
    report_date = generated_at.date().isoformat()

    bookmark_cards = render_cards(
        bookmarks,
        tweet_card,
        "No authenticated X bookmarks were captured.",
    )
    top_post_cards = render_cards(
        top_posts,
        tweet_card,
        "No top X posts were captured for the configured lookback window.",
    )
    github_cards = render_cards(github, github_card, "GitHub Trending returned no parsed projects.")
    paper_cards = render_cards(papers, paper_card, "Hugging Face Papers returned no parsed papers.")
    run_notes = run_note_section(public_notes, x_notes)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)} - {report_date}</title>
  <link rel="icon" href="data:,">
  <style>
    :root {{
      --color-gray-50: #f9fafb;
      --color-gray-100: #f3f4f6;
      --color-gray-200: #e5e7eb;
      --color-gray-300: #d1d5db;
      --color-gray-600: #4b5563;
      --color-gray-900: #111827;
      --color-blue: #1e40af;
      --color-canvas: canvas;
    }}

    * {{ box-sizing: border-box; }}

    html {{
      background: var(--color-gray-50);
    }}

    body {{
      margin: 0;
      color: var(--color-gray-900);
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--color-gray-50);
      font-size: 0.875rem;
      line-height: 1.5;
      -webkit-font-smoothing: antialiased;
    }}

    a {{ color: inherit; text-decoration: none; }}
    a:hover {{ text-decoration: underline; text-underline-offset: 3px; }}
    a:focus-visible, summary:focus-visible {{
      outline: 2px solid var(--color-blue);
      outline-offset: 2px;
    }}

    .shell {{
      width: min(1040px, calc(100% - 32px));
      margin: 0 auto;
    }}

    .hero {{
      padding: 24px 0 16px;
      background: var(--color-canvas);
      border-bottom: 1px solid var(--color-gray-200);
    }}

    .hero-row {{
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      gap: 16px;
      flex-wrap: wrap;
    }}

    .kicker {{
      margin: 0 0 4px;
      color: var(--color-gray-600);
      font-size: 0.75rem;
      font-weight: 500;
      letter-spacing: 0;
    }}

    h1 {{
      margin: 0;
      font-size: 1.875rem;
      line-height: 2.25rem;
      letter-spacing: 0;
      font-weight: 600;
    }}

    .date-block {{
      min-width: 176px;
      padding: 10px 12px;
      border: 1px solid var(--color-gray-200);
      border-radius: 0.5rem;
      background: var(--color-canvas);
      text-align: right;
    }}

    .date-block strong {{
      display: block;
      font-size: 0.875rem;
      line-height: 1.25rem;
      font-weight: 600;
    }}

    .date-block span {{
      color: var(--color-gray-600);
      font-size: 0.75rem;
      line-height: 1rem;
    }}

    .section {{
      padding: 20px 0;
      border-top: 1px solid var(--color-gray-200);
    }}

    .section-head {{
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 10px;
    }}

    h2 {{
      margin: 0;
      font-size: 1.125rem;
      line-height: 1.75rem;
      letter-spacing: 0;
      font-weight: 600;
    }}

    .section-head p {{
      margin: 0;
      color: var(--color-gray-600);
      font-size: 0.875rem;
      line-height: 1.25rem;
    }}

    .item-grid {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 8px;
    }}

    .item-card {{
      min-height: 0;
      padding: 12px;
      border: 1px solid var(--color-gray-200);
      border-radius: 0.5rem;
      background: var(--color-canvas);
      transition: border-color 120ms ease, background 120ms ease;
    }}

    .item-card:hover {{
      border-color: var(--color-gray-300);
      background: var(--color-gray-100);
    }}

    .item-top {{
      display: flex;
      gap: 10px;
      align-items: baseline;
      min-width: 0;
    }}

    .item-rank {{
      flex: 0 0 auto;
      color: var(--color-gray-600);
      font-size: 0.75rem;
      font-weight: 500;
      line-height: 1rem;
      letter-spacing: 0;
      font-variant-numeric: tabular-nums;
    }}

    .item-title {{
      min-width: 0;
      color: var(--color-blue);
      font-weight: 500;
      font-size: 0.875rem;
      line-height: 1.25rem;
      overflow-wrap: anywhere;
    }}

    .item-text {{
      margin: 6px 0 0;
      color: var(--color-gray-600);
      font-size: 0.875rem;
      line-height: 1.5;
    }}

    .item-details {{
      margin-top: 8px;
      border-top: 1px solid var(--color-gray-200);
      padding-top: 8px;
    }}

    .item-details summary {{
      width: fit-content;
      cursor: pointer;
      user-select: none;
      color: var(--color-gray-600);
      font-size: 0.75rem;
      line-height: 1rem;
      font-weight: 500;
      list-style: none;
      border-radius: 0.25rem;
    }}

    .item-details summary::-webkit-details-marker {{ display: none; }}

    .item-details summary::after {{
      content: " +";
      color: var(--color-gray-600);
      font-weight: 700;
    }}

    .item-details[open] summary::after {{
      content: " -";
    }}

    .detail-copy {{
      margin-top: 8px;
      padding: 10px;
      border-radius: 0.375rem;
      background: var(--color-gray-50);
      color: var(--color-gray-600);
      font-size: 0.875rem;
      line-height: 1.5;
    }}

    .detail-copy p {{
      margin: 0;
    }}

    .detail-copy p + p {{
      margin-top: 8px;
    }}

    .metric-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
      margin-top: 8px;
    }}

    .metric-row span {{
      display: inline-flex;
      gap: 4px;
      align-items: baseline;
      padding: 2px 6px;
      border: 1px solid var(--color-gray-200);
      border-radius: 0.375rem;
      background: var(--color-gray-50);
      color: var(--color-gray-600);
      font-size: 0.75rem;
      line-height: 1rem;
    }}

    .metric-row strong {{
      color: var(--color-gray-900);
      font-size: 0.75rem;
      font-weight: 500;
    }}

    .run-notes {{
      margin: 0;
      padding: 0;
      list-style: none;
      display: grid;
      gap: 8px;
    }}

    .run-notes li, .empty-state {{
      padding: 10px 12px;
      border: 1px solid var(--color-gray-200);
      border-radius: 0.5rem;
      background: var(--color-canvas);
      color: var(--color-gray-600);
      line-height: 1.5;
    }}

    footer {{
      padding: 16px 0 32px;
      color: var(--color-gray-600);
      font-size: 0.75rem;
      line-height: 1rem;
      border-top: 1px solid var(--color-gray-200);
    }}

    @media (max-width: 640px) {{
      .shell {{
        width: min(100% - 24px, 1040px);
      }}

      .hero-row, .section-head {{
        align-items: flex-start;
      }}

      .hero {{
        padding-top: 18px;
      }}

      .date-block {{
        width: 100%;
        text-align: left;
      }}
    }}

    @media print {{
      body {{ background: #fff; }}
      .item-card, .run-notes li {{ break-inside: avoid; }}
      a {{ color: #000; }}
    }}
  </style>
</head>
<body>
  <header class="hero">
    <div class="shell">
      <div class="hero-row">
        <div>
          <p class="kicker">Daily Brief</p>
          <h1>{escape(title)}</h1>
        </div>
        <div class="date-block">
          <strong>{report_date}</strong>
          <span>Generated {escape(generated_at.strftime('%H:%M %Z'))}</span>
        </div>
      </div>
    </div>
  </header>

  <main class="shell">
    <section class="section">
      <div class="section-head">
        <h2>Latest X Bookmarks</h2>
      </div>
      <div class="item-grid">
{bookmark_cards}
      </div>
    </section>

    <section class="section">
      <div class="section-head">
        <h2>Top X Posts</h2>
      </div>
      <div class="item-grid">
{top_post_cards}
      </div>
    </section>

    <section class="section">
      <div class="section-head">
        <h2>GitHub Projects</h2>
      </div>
      <div class="item-grid">
{github_cards}
      </div>
    </section>

    <section class="section">
      <div class="section-head">
        <h2>HF Papers</h2>
      </div>
      <div class="item-grid">
{paper_cards}
      </div>
    </section>
{run_notes}
  </main>

  <footer>
    <div class="shell">Generated {escape(generated_at.strftime('%Y-%m-%d %H:%M %Z'))}</div>
  </footer>
</body>
</html>
"""


def build_markdown(public: dict, x_data: dict, config: dict, generated_at: dt.datetime) -> str:
    output_cfg = config.get("output", {})
    top_github = int(output_cfg.get("top_github_projects", 5))
    top_papers = int(output_cfg.get("top_huggingface_papers", 5))

    bookmarks = x_data.get("x_bookmarks", [])
    top_posts = x_data.get("top_x_posts", [])
    github = public.get("github_trending", [])[:top_github]
    papers = public.get("huggingface_papers", [])[:top_papers]
    public_notes = public.get("access_notes", [])
    x_notes = x_data.get("access_notes", [])

    lines = [
        f"# Morning Brief - {generated_at.date().isoformat()}",
        "",
        f"Generated: {generated_at.strftime('%Y-%m-%d %H:%M %Z')}",
        "",
        "## Latest X Bookmarks",
        "",
    ]

    if bookmarks:
        for item in bookmarks:
            lines.append(tweet_line(item))
    else:
        lines.append("- No authenticated X bookmarks were captured.")

    lines.extend(["", "## Top X Posts", ""])
    if top_posts:
        for item in top_posts:
            lines.append(tweet_line(item))
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

    if public_notes or x_notes:
        lines.extend(["", "## Run Notes", ""])
    for note in [*public_notes, *x_notes]:
        lines.append(f"- {note}")
    if public_notes or x_notes:
        lines.append("")
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
    public = run_json_safe(
        ["python3", "scripts/fetch_public_sources.py"],
        timeout=60,
        fallback={"github_trending": [], "huggingface_papers": []},
        label="Public source fetch",
    )

    if args.skip_x:
        x_data = {"x_bookmarks": [], "top_x_posts": [], "access": {"method": "skipped"}, "meta": {}}
    else:
        x_data = run_json_safe(
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
            fallback={
                "x_bookmarks": [],
                "top_x_posts": [],
                "access": {"method": "unavailable"},
                "meta": {},
            },
            label="X fetch",
        )

    report_dir = ROOT / config.get("report_directory", "reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    output_format = str(output_cfg.get("format", "html")).lower()
    if output_format == "markdown":
        report_path = report_dir / f"{report_date}.md"
        report_path.write_text(build_markdown(public, x_data, config, generated_at), encoding="utf-8")
    else:
        report_path = report_dir / f"{report_date}.html"
        report_path.write_text(build_html(public, x_data, config, generated_at), encoding="utf-8")
    print(str(report_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
