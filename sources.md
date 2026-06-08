# Source Plan

Use this file to pin specific sources for the morning brief as the automation becomes more precise.

## X/Twitter Bookmarks

- Use authenticated browser access if available.
- If bookmark access is unavailable, note that in the brief and skip this section rather than guessing.
- This is the main source that may require Playwright, Chrome, or another authenticated browser tool.

## X/Twitter Threads

- Find the most important public threads from the last 24 hours across AI, business, and startups.
- Prioritize credible operators, founders, investors, researchers, and builders.
- Favor posts with concrete data, useful strategy, practical implementation detail, or strong community momentum.
- Try public search/simple web discovery first, but use authenticated browser access when X blocks public results.

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
