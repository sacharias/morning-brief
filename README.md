# Morning Brief

Daily morning intelligence brief focused on AI, business, startups, open-source projects, and research.

## Schedule

- Runs every morning at 08:00 Europe/Stockholm unless changed in Codex.

## Sources

- X/Twitter bookmarks: latest saved posts and threads, if authenticated access is available.
- X/Twitter public threads: top 10 important threads from the last 24 hours in AI, business, and startups.
- GitHub Trending: top 5 new or newly relevant trending projects.
- Hugging Face Papers: top 5 popular papers.

## Tool Policy

- Use the simplest reliable tool for each source.
- Use `curl` and lightweight parsing for public sources such as GitHub Trending and Hugging Face Papers.
- Use Playwright/Chrome only for sources that need authenticated browser state, mainly X/Twitter bookmarks and authenticated X search.

## Scripts

- `scripts/fetch_public_sources.py` fetches GitHub Trending and Hugging Face Papers through `curl` and emits JSON.
- `scripts/fetch_x_sources.js` launches real Chrome with a temporary copy of the current Chrome profile files, captures authenticated X GraphQL responses, and emits sanitized JSON.
- `scripts/create_morning_brief.py` combines the public and X sources and writes `reports/YYYY-MM-DD.md`.

Run:

```bash
npm run brief
```

## Output

Each run should produce a concise Markdown brief with:

- Executive summary.
- X bookmarks worth revisiting.
- Top AI/business/startup X threads.
- Trending GitHub projects.
- Hugging Face papers.
- Recommended follow-ups.
- Source links and access notes.

Reports are saved in `reports/YYYY-MM-DD.md`.
