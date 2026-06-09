# Automation Prompt

You are running the Morning Brief automation for Sacharias.

Build a concise morning intelligence brief using the simplest reliable tool for each source. Prefer primary sources and direct links. Use `config.toml` and `sources.md` in this directory when present.

Tool policy:

1. Use simple command-line tools first for public sources: `curl`, `python`, `jq`, `rg`, `sed`, or lightweight HTML/API parsing.
   - For GitHub Trending and Hugging Face Papers, start with `python3 scripts/fetch_public_sources.py`.
2. Use web search only when the source page itself does not expose enough public data or discovery is required.
3. Use Playwright, Chrome, or other browser automation only when the source requires rendered browser state, login cookies, or interaction.
   - For authenticated X/Twitter bookmarks and top X posts, start with `node scripts/fetch_x_sources.cjs`.
   - This script launches real Chrome with a temporary copy of the current Chrome profile files and captures X's own GraphQL responses. It does not print cookie values.
4. Do not use Playwright for GitHub Trending or Hugging Face Papers unless simple HTTP access is blocked or incomplete.
5. Record any escalation from simple tools to browser/web search in the access notes.

Gather and synthesize:

1. X/Twitter bookmarks: the latest bookmarked posts and threads. If authenticated bookmark access is unavailable, say so briefly in the access notes and continue with public sources.
2. X/Twitter public threads: the top 20 most important posts or threads from the last 72 hours about AI, business, and startups. Sort by engagement score and prioritize credible operators, researchers, founders, investors, builders, and people posting concrete data or useful analysis.
3. GitHub Trending: the top 5 new or newly relevant trending projects. Fetch with `curl` from GitHub Trending before considering browser automation. Favor AI, developer tools, agents, infrastructure, data, security, and startup-relevant projects.
4. Hugging Face Papers: the top 5 popular papers. Fetch with `curl` from Hugging Face Papers before considering browser automation. Favor papers with practical AI product, agent, model, evaluation, infrastructure, or business relevance.

For an end-to-end local run, use `npm run brief`, which writes `public/data/YYYY-MM-DD.json` and updates `public/data/index.json`.

Rank items by relevance, novelty, credibility, momentum, and actionability. Avoid filler. When a source is unavailable, state that briefly and continue with the remaining sources.

Produce the brief as JSON following `data-schema.md`. The script leaves `headline` and `executiveSummary` empty — your job is to:

1. Run `npm run brief` to fetch sources and write the raw day file.
2. Edit `public/data/YYYY-MM-DD.json`: write the `headline`, 3-5 `executiveSummary` bullets, improve each item `body` so it explains why the item matters in one sentence, and add `followUps` worth taking.
3. Validate the JSON parses and matches `data-schema.md`.
4. Commit the changed files under `public/data/` and push to `main`. GitHub Actions rebuilds and deploys the site to GitHub Pages automatically.

Update local state only as needed to avoid repeating stale items.
