# Morning Brief

Daily morning intelligence brief focused on AI, business, startups, open-source projects, and research.

Live site: https://sacharias.github.io/morning-brief/

## How it works

- A mobile-first Vite + React app renders JSON from `public/data/` — all prose and data live in the JSON, none in the app (see `data-schema.md`).
- An AI agent on a cron job runs the fetch scripts each morning, writes `public/data/YYYY-MM-DD.json`, updates `public/data/index.json`, refreshes `reports/YYYY-MM-DD.md` as a local sidecar report, verifies the site build, and pushes the website changes to `main` (see `automation-prompt.md`).
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
- `scripts/fetch_x_sources.cjs` captures authenticated X GraphQL responses and emits sanitized JSON. It can reuse a logged-in Chrome/Chromium profile, reuse saved Playwright auth state from ignored local state, or log in with runtime username/password environment variables.
- `scripts/create_morning_brief.py` combines the public and X sources, writes `public/data/YYYY-MM-DD.json`, updates `public/data/index.json`, and writes `reports/YYYY-MM-DD.md`.

Run:

```bash
npm run brief
```

Authenticated X options:

```bash
# Interactive browser-profile setup; stores local browser state under ignored state/.
npm run setup:x-auth

# Non-interactive credential login; values must be supplied only at runtime.
MORNING_BRIEF_X_USERNAME=... MORNING_BRIEF_X_PASSWORD=... npm run fetch:x:login

# Later runs reuse ignored state/x-storage-state.json when it is still valid.
npm run fetch:x
```

Supported X environment variables:

- `MORNING_BRIEF_X_USERNAME` and `MORNING_BRIEF_X_PASSWORD` for runtime credential login.
- `MORNING_BRIEF_X_STORAGE_STATE` to override the ignored Playwright storage-state path. Default: `state/x-storage-state.json`.
- `MORNING_BRIEF_X_CHROME_USER_DATA_DIR`, `MORNING_BRIEF_X_CHROME_PROFILE`, and `MORNING_BRIEF_X_BROWSER_CHANNEL` for Chrome/Chromium profile reuse.

If X asks for CAPTCHA, 2FA, SMS/email verification, passkey, or another anti-abuse challenge, the fetch reports that blocker in run notes and leaves public sources available.

After editing the generated JSON editorial fields, refresh the Markdown report:

```bash
npm run report -- --date YYYY-MM-DD
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
