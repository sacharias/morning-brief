# Source Plan

Use this file to pin specific sources for the morning brief as the automation becomes more precise.

## X/Twitter Bookmarks

- Use `node scripts/fetch_x_sources.cjs` for authenticated access.
- The script launches real Chrome with a temporary copy of the current Chrome `Default` profile files, lets Chrome decrypt its own session cookies, captures X GraphQL responses, and deletes the temporary profile after the run.
- If bookmark access is unavailable, note that in the brief and skip this section rather than guessing.
- Keep cookie values out of logs and report output.

## X/Twitter Threads

- Find the most important public posts and threads from the last 72 hours across AI, business, and startups.
- Prioritize credible operators, founders, investors, researchers, and builders.
- Favor posts with concrete data, useful strategy, practical implementation detail, or strong community momentum.
- Use `node scripts/fetch_x_sources.cjs`; it captures authenticated `SearchTimeline` responses and filters/ranks posts in the configured lookback window by engagement score.
- Render only the top 8-12 posts after curation. Repetition, listicles, giveaways, and generic model hype should be cut even when engagement is high.

## GitHub Trending

- Use GitHub Trending and direct repository pages.
- Return the top 8 new or newly relevant projects.
- Prioritize AI, agents, developer tools, infrastructure, data, security, and startup-relevant repositories.
- Prefer `curl` and lightweight parsing. Do not use Playwright unless GitHub blocks simple HTTP access or the page shape changes enough that parsing fails.

## Hugging Face Papers

- Use Hugging Face Papers and primary paper/project pages.
- Return the top 5 popular papers.
- Prioritize practical relevance to AI products, agents, model evaluation, model infrastructure, and business use.
- Prefer `curl` and lightweight parsing. Do not use Playwright unless Hugging Face blocks simple HTTP access or the page shape changes enough that parsing fails.

## Founder Signals (Asks / Proof / Launches)

- Use `python3 scripts/fetch_founder_signals.py` for all three lists.
- Asks (demand): HN Algolia search ("Ask HN" plus queries like "I'd pay for", "is there a tool that", "looking for a tool") and Reddit daily top JSON for the configured founder subs. Keep posts whose titles read as a request or complaint ("how do you", "is there", "i wish", "alternative to", "i'd pay", …) or that show high engagement in founder subs.
- Proof (revenue): r/indiehackers, r/SaaS, and r/SideProject posts matching revenue patterns (`$`, MRR, ARR, "first customer", "sold my", "acquired"), plus HN Algolia "Show HN" + revenue terms.
- Launches: the Product Hunt Atom feed. Best-effort; note failures in access notes.
- Favor concrete, specific pain and real numbers from people who appear to build or pay. Cut vague rants, engagement bait, link-less hype, and anything older than the configured lookback.
- Render no more than 6 Asks, 4 Proof items, and 5 Launches.

## Shipped

- Use `python3 scripts/fetch_shipped.py`.
- Vendor release feeds (OpenAI, Anthropic, Google AI, Meta AI, Hugging Face, DeepMind — list in `config.toml`), Hugging Face trending models via the models API, and GitHub release Atom feeds for the pinned repos.
- Keep entries from the configured lookback window, sorted newest first.
- Favor releases a solo builder can act on this week: new models, new APIs and SDKs, pricing changes, capability unlocks. Cut pure PR posts and research-only announcements.
- Render no more than 8 Shipped items.

## Hidden Scouting

- Use `python3 scripts/fetch_hidden_scouting.py` to collect raw clues for synthesis.
- Sources: HN comments, GitHub issue search, and watched docs/pricing/model pages from `config.toml`.
- The script writes raw clues into `sourceSignals`; the website does not render them directly.
- Use these clues to produce exactly 3 front-page `hidden-signals` items. Each hidden signal must cross at least two independent evidence links and explain:
  - the signal,
  - the evidence,
  - why others are likely missing it,
  - what the reader should do.
- Strong hidden signals usually come from comments, issues, docs/pricing changes, obscure repo acceleration, or release details before the same pattern shows up as a launch.

## Verdicts

- Every kept item should carry `verdict: "act"`, `"watch"`, or `"ignore"`.
- `act`: do something this week.
- `watch`: meaningful but not immediate.
- `ignore`: visible but low-value noise the reader should explicitly deprioritize.

## X data for Asks / Proof

- Authenticated X search data (via `node scripts/fetch_x_sources.cjs`) may additionally feed the Asks and Proof sections — the agent curates relevant pain-point and revenue posts in, alongside the scripted sources.
