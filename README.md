# Morning Brief

Daily morning intelligence brief focused on AI, business, startups, open-source projects, and research.

Live site: https://sacharias.github.io/morning-brief/

## How it works

- A mobile-first Vite + React app renders JSON from `public/data/` — all prose and data live in the JSON, none in the app (see `data-schema.md`).
- An AI agent on a cron job runs the fetch scripts each morning, writes `public/data/YYYY-MM-DD.json`, updates `public/data/index.json`, verifies the site build, and pushes the website changes to `main` (see `automation-prompt.md`).
- GitHub Actions builds and deploys to GitHub Pages on every push to `main`.

Local development: `npm install && npm run dev`.

## Schedule

- Runs every morning at 08:00 Europe/Stockholm unless changed in Codex.

## Sources

- X/Twitter bookmarks: latest saved posts and threads, if authenticated access is available.
- X/Twitter public threads: top 20 important posts/threads from the last 72 hours in AI, business, and startups, sorted by engagement score.
- GitHub Trending: top 5 new or newly relevant trending projects.
- Hugging Face Papers: top 5 popular papers.

## Tool Policy

- Use the simplest reliable tool for each source.
- Use `curl` and lightweight parsing for public sources such as GitHub Trending and Hugging Face Papers.
- Use Playwright/Chrome only for sources that need authenticated browser state, mainly X/Twitter bookmarks and authenticated X search.

## Scripts

- `scripts/fetch_public_sources.py` fetches GitHub Trending and Hugging Face Papers through `curl` and emits JSON.
- `scripts/fetch_custom_trending.py` runs our own trending algorithm (24h star acceleration vs the prior week) against the public ClickHouse playground's `github_events` dataset.
- `scripts/fetch_x_sources.cjs` launches real Chrome with a temporary copy of the current Chrome profile files, captures authenticated X GraphQL responses, and emits sanitized JSON.
- `scripts/create_morning_brief.py` combines the public and X sources, writes `public/data/YYYY-MM-DD.json`, and updates `public/data/index.json`.

Run:

```bash
npm run brief
```

## Output

Each run should produce a concise HTML brief with:

- Executive summary.
- X bookmarks worth revisiting.
- Top AI/business/startup X threads.
- Trending GitHub projects.
- Hugging Face papers.
- Recommended follow-ups.
- Source links and access notes.

The deployed website is rebuilt from the repo on every push to `main`.
