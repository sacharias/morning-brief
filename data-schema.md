# Brief data schema

All content the site displays lives in `public/data/`. The React app contains no
prose of its own — an agent updates these JSON files each morning, commits, and
pushes; GitHub Actions rebuilds and deploys the site automatically.

## Files

- `public/data/index.json` — list of available days:

```json
{
  "latest": "2026-06-09",
  "days": ["2026-06-09", "2026-06-08"]
}
```

`days` is sorted newest first. The app loads `latest` by default and offers a
date picker when more than one day exists.

- `public/data/YYYY-MM-DD.json` — one brief per day:

```json
{
  "date": "2026-06-09",
  "generatedAt": "2026-06-09T08:00:00+02:00",
  "headline": "One-sentence editorial headline for the day.",
  "executiveSummary": [
    "Three to five bullets capturing the most important signals of the day."
  ],
  "sections": [
    {
      "id": "kebab-case-stable-id",
      "title": "Section Title",
      "page": "x",
      "description": "Optional one-line subtitle.",
      "emptyMessage": "Shown when items is empty.",
      "previewCount": 6,
      "items": [
        {
          "title": "Display title (@handle, repo name, or paper title)",
          "url": "https://… (optional; title renders as plain text without it)",
          "body": "Prose summary of the item. Write it for a human reader.",
          "metrics": [{ "label": "likes", "value": "12,400" }],
          "tags": ["AI", "agents"]
        }
      ]
    }
  ],
  "followUps": ["Optional list of recommended follow-up actions."],
  "runNotes": ["Optional operational notes (failed sources, access issues)."]
}
```

## Rules for agents

- Every string the reader sees comes from this JSON: headline, summaries,
  section titles, item prose. Write complete, human-quality prose — the app
  does no rewriting.
- Section `id`s should stay stable day to day (`x-bookmarks`, `top-x-posts`,
  `github-trending`, `custom-trending`, `hf-papers`) so anchors keep working;
  adding new sections is fine.
- The app is a tabbed mobile layout. `page` assigns a section to a bottom tab:
  `x`, `code`, or `papers`; anything else (or omitted with an unknown id)
  renders on the Today tab. Sections render in array order within a page, so
  keep `x-bookmarks` after `top-x-posts` — bookmarks belong at the bottom.
  Multiple sections on the `code` page render as a segmented toggle.
- `metrics` and `tags` are optional arrays; omit them rather than leaving
  empty placeholders.
- Sections with more items than `previewCount` (default 6) render the first
  `previewCount` items with a "Show all N" toggle for the rest, so long
  sections (20 bookmarks, 40 posts) stay scannable.
- Always update `index.json` when adding a day. Keep old day files — the site
  is the archive.
- `scripts/create_morning_brief.py` fetches sources and writes a valid day
  file with `headline`/`executiveSummary` left empty; the agent's job is to
  fill those in (and improve item `body` prose) before committing.
