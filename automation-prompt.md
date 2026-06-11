# Automation Prompt

You are running the Morning Brief website automation for Sacharias.

This repository is a deployable website. Your job is to refresh today's site content, verify the site still builds, then publish the updated website to GitHub. Use `config.toml` and `sources.md` in this directory when present.

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
5. Founder signals: demand posts (Asks), revenue proof, and Product Hunt launches via `python3 scripts/fetch_founder_signals.py` (already wired into `npm run brief`).
6. Shipped: vendor releases, trending models, and pinned-repo releases via `python3 scripts/fetch_shipped.py` (already wired into `npm run brief`).

For an end-to-end local run, use `npm run brief`, which writes `public/data/YYYY-MM-DD.json` and updates `public/data/index.json`.

Rank items by relevance, novelty, credibility, momentum, and actionability. Avoid filler. When a source is unavailable, state that briefly and continue with the remaining sources.

Treat the generated JSON as the website's content source of truth. The script leaves `headline` and `executiveSummary` empty — your job is to:

1. Run `npm run brief` to fetch sources and write the raw day file.
2. Edit `public/data/YYYY-MM-DD.json`: write the `headline`, 3-5 `executiveSummary` bullets, improve each item `body` so it explains why the item matters in one sentence, and add `followUps` worth taking.
3. Curate the Asks, Proof, and Launches sections: cut weak items and write each `body` as one sentence on why it matters to a builder.
4. Annotate every kept Shipped item with one clause on what it unlocks for a solo builder.
5. Rewrite each item body in the `developing` section as a delta — "Day N of X — what changed: …". Drop items with nothing new.
6. Update the build-idea ledger (see below) and ensure the `build-ideas` section reflects it.
7. Validate the JSON parses and matches `data-schema.md`.
8. Run `npm run build` to verify the website still compiles.
9. Review `git status` and commit the website changes needed for this update. By default that includes `public/data/` and `state/idea_ledger.json`; if you had to make a targeted site or automation fix, include those repo files too.
10. Push to `main`. GitHub Actions rebuilds and deploys the site to GitHub Pages automatically.

Build ideas and the ledger:

1. Each run, propose 1-2 build ideas by crossing the day's signals: a paper or shipped capability × a demand signal × no incumbent in the launches.
2. Update `state/idea_ledger.json`: add new ideas, append evidence (date, url, note) to existing ideas when a new signal supports them, mark an idea `taken` when a launch claims it, `validated` once it has evidence from 3 or more days, and `dead` after roughly 7 days without new evidence.
3. Ensure the `build-ideas` section reflects the ledger, then commit the ledger alongside the day file.

Constraints:

1. Keep fixes scoped to this repository.
2. Prefer minimal targeted changes over refactors.
3. Do not modify unrelated local files outside this repo.
4. If a source is down or authentication fails, note it in `runNotes`, keep the website publishable, and still push the updated site.

Update local state only as needed to avoid repeating stale items.
