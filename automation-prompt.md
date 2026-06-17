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
2. X/Twitter public threads: keep only the top 8-12 important posts or threads from the last 72 hours about AI, business, and startups. Sort by engagement score and prioritize credible operators, researchers, founders, investors, builders, and people posting concrete data or useful analysis.
3. GitHub Trending: keep only the top 8 new or newly relevant projects. Fetch with `curl` from GitHub Trending before considering browser automation. Favor AI, developer tools, agents, infrastructure, data, security, and startup-relevant projects.
4. Hugging Face Papers: keep only the top 5 popular papers. Fetch with `curl` from Hugging Face Papers before considering browser automation. Favor papers with practical AI product, agent, model, evaluation, infrastructure, or business relevance.
5. Founder signals: demand posts (Asks), revenue proof, and Product Hunt launches via `python3 scripts/fetch_founder_signals.py` (already wired into `npm run brief`).
6. Shipped: vendor releases, trending models, and pinned-repo releases via `python3 scripts/fetch_shipped.py` (already wired into `npm run brief`).
7. Hidden scouting: raw HN comments, GitHub issue searches, and watched docs/pricing diffs via `python3 scripts/fetch_hidden_scouting.py` (already wired into `npm run brief`). These populate `sourceSignals`; do not publish them directly.

For an end-to-end local run, use `npm run brief`, which writes `public/data/YYYY-MM-DD.json`, updates `public/data/index.json`, and creates the initial `reports/YYYY-MM-DD.md` sidecar report.

Rank items by relevance, novelty, credibility, momentum, and actionability. Avoid filler. When a source is unavailable, state that briefly and continue with the remaining sources.

The Today page is the hard front page. It should contain only the headline, 3-5 executive summary bullets, exactly 3 hidden signals, no more than 3 follow-ups, and collapsed run notes. The X / Code / Papers / Build tabs are finite drilldowns, not another feed.

Treat the generated JSON as the website's content source of truth. The script leaves `headline` and `executiveSummary` empty — your job is to:

1. Run `npm run brief` to fetch sources and write the raw day file.
2. Edit `public/data/YYYY-MM-DD.json`: write the `headline`, 3-5 `executiveSummary` bullets, improve each item `body` so it explains why the item matters in one sentence, and cap `followUps` at 3 worthwhile actions.
3. Write exactly 3 `hidden-signals` items by crossing `sourceSignals` with the day's X, code, papers, shipped, demand, proof, and launch sections. Each hidden signal must use the format "Signal -> Evidence -> Why others miss it -> What to do" in concise prose and include at least two independent `evidence` links.
4. Set every kept item `verdict` to `act`, `watch`, or `ignore`. Use `ignore` sparingly and only when explicitly useful to tell the reader to skip a noisy but visible item.
5. Curate the Asks, Proof, and Launches sections: cut weak items and write each `body` as one sentence on why it matters to a builder. Keep no more than 6 Asks, 4 Proof items, and 5 Launches.
6. Annotate every kept Shipped item with one clause on what it unlocks for a solo builder. Keep no more than 8 Shipped items.
7. Rewrite each item body in the `developing` section as a true delta — "Day N of X - what changed: …". Drop items whose only update is that they are still trending, still relevant, or still popular.
8. Update the build-idea ledger (see below) and ensure the `build-ideas` section reflects it with evidence count, latest evidence, and `whyNow` when today's signals add urgency.
9. Keep the published brief under 60 total rendered items. Prefer cutting sections over keeping borderline items.
10. Refresh the Markdown sidecar with `npm run report -- --date YYYY-MM-DD` after the JSON editorial pass, so `reports/YYYY-MM-DD.md` reflects the final brief.
11. Validate the JSON parses and passes the quality gate with `npm run validate:brief -- --date YYYY-MM-DD`.
12. Run `npm run build` to verify the website still compiles.
13. Review `git status` and commit the website changes needed for this update. By default that includes `public/data/`, `reports/`, `state/idea_ledger.json`, and `state/hidden_scouting_pages.json`; if you had to make a targeted site or automation fix, include those repo files too.
14. Push to `main`. GitHub Actions rebuilds and deploys the site to GitHub Pages automatically.

Build ideas and the ledger:

1. Each run, propose 1-2 build ideas by crossing the day's signals: a paper or shipped capability × a demand signal × no incumbent in the launches.
2. Update `state/idea_ledger.json`: add new ideas, append evidence (date, url, note) to existing ideas when a new signal supports them, mark an idea `taken` when a launch claims it, `validated` once it has evidence from 3 or more days, and `dead` after roughly 7 days without new evidence.
3. For each open or validated idea, keep `summary` buyer-specific, add `whyNow` when the current day materially changes timing, and ensure the rendered item has latest evidence.
4. Ensure the `build-ideas` section reflects the ledger, then commit the ledger alongside the day file.

Quality bar:

1. High value/noise ratio wins over completeness. If a reader would not act, watch, or explicitly ignore it, cut it.
2. The best hidden signals should feel early: issue/comment pain, docs/pricing changes, release diffs, paper methods, or obscure repo acceleration before Product Hunt turns it into launch theater.
3. Do not summarize sources one by one on Today. Name the pattern, cite the evidence, and say what to do.
4. Repeated items must have a real delta. "Still trending", "remains relevant", and "continues to get attention" are not enough.

Constraints:

1. Keep fixes scoped to this repository.
2. Prefer minimal targeted changes over refactors.
3. Do not modify unrelated local files outside this repo.
4. If a source is down or authentication fails, note it in `runNotes`, keep the website publishable, and still push the updated site.

Update local state only as needed to avoid repeating stale items.
