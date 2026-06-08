# Source Plan

Use this file to pin specific sources for the morning brief as the automation becomes more precise.

## X/Twitter Bookmarks

- Use `node scripts/fetch_x_sources.js` for authenticated access.
- The script launches real Chrome with a temporary copy of the current Chrome `Default` profile files, lets Chrome decrypt its own session cookies, captures X GraphQL responses, and deletes the temporary profile after the run.
- If bookmark access is unavailable, note that in the brief and skip this section rather than guessing.
- Keep cookie values out of logs and report output.

## X/Twitter Threads

- Find the most important public posts and threads from the last 72 hours across AI, business, and startups.
- Prioritize credible operators, founders, investors, researchers, and builders.
- Favor posts with concrete data, useful strategy, practical implementation detail, or strong community momentum.
- Use `node scripts/fetch_x_sources.js`; it captures authenticated `SearchTimeline` responses and filters/ranks posts in the configured lookback window by engagement score.

## GitHub Trending

- Use GitHub Trending and direct repository pages.
- Return the top 5 new or newly relevant projects.
- Prioritize AI, agents, developer tools, infrastructure, data, security, and startup-relevant repositories.
- Prefer `curl` and lightweight parsing. Do not use Playwright unless GitHub blocks simple HTTP access or the page shape changes enough that parsing fails.

## Hugging Face Papers

- Use Hugging Face Papers and primary paper/project pages.
- Return the top 5 popular papers.
- Prioritize practical relevance to AI products, agents, model evaluation, model infrastructure, and business use.
- Prefer `curl` and lightweight parsing. Do not use Playwright unless Hugging Face blocks simple HTTP access or the page shape changes enough that parsing fails.
