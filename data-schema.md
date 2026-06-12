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
      "shortTitle": "Optional label for segmented-control pills",
      "page": "x",
      "description": "Optional one-line subtitle.",
      "emptyMessage": "Shown when items is empty.",
      "items": [
        {
          "title": "Display title (@handle, repo name, or paper title)",
          "url": "https://… (optional; title renders as plain text without it)",
          "body": "Prose summary of the item. Write it for a human reader.",
          "metrics": [{ "label": "likes", "value": "12,400" }],
          "tags": ["AI", "agents"],
          "isNew": true,
          "previously": [{ "date": "2026-06-08" }]
        }
      ]
    }
  ],
  "followUps": ["Optional list of recommended follow-up actions."],
  "runNotes": ["Optional operational notes (failed sources, access issues)."]
}
```

- `reports/YYYY-MM-DD.md` — a generated Markdown sidecar for the same brief.
  The website does not read this file; it is a local/reporting artifact built
  from the JSON. Run `npm run report -- --date YYYY-MM-DD` after editing the
  JSON so the report reflects the final headline, summaries, item bodies, and
  follow-ups.

- `state/idea_ledger.json` — the persistent build-idea ledger. The nightly
  agent creates and updates ideas; the build script renders open + validated
  ideas into the `build-ideas` section. Unlike the rest of `state/`, this file
  is committed to git — it must persist across runs and machines.

```json
{
  "ideas": [
    {
      "id": "kebab-slug",
      "title": "Short idea name",
      "summary": "One-paragraph pitch: the problem, who pays, the wedge.",
      "status": "open",
      "created": "YYYY-MM-DD",
      "updated": "YYYY-MM-DD",
      "evidence": [
        { "date": "YYYY-MM-DD", "url": "https://…", "note": "what this signal showed" }
      ]
    }
  ]
}
```

`status` is one of `open`, `validated`, `taken`, or `dead`.

## Rules for agents

- Every string the reader sees comes from this JSON: headline, summaries,
  section titles, item prose. Write complete, human-quality prose — the app
  does no rewriting.
- Section `id`s should stay stable day to day (`x-bookmarks`, `top-x-posts`,
  `github-trending`, `custom-trending`, `hf-papers`, `demand-signals`,
  `revenue-proof`, `build-ideas`, `launches`, `shipped`, `developing`) so
  anchors keep working; adding new sections is fine.
- The app is a tabbed mobile layout. `page` assigns a section to a bottom tab:
  `x`, `code`, `papers`, or `build`; anything else (or omitted with an unknown
  id) renders on the Today tab. Sections render in array order within a page,
  so keep `x-bookmarks` after `top-x-posts` — bookmarks belong at the bottom.
  Multiple sections on the `x`, `code`, or `build` pages render as a segmented
  toggle (labelled by `shortTitle` when present).
- Founder sections live on fixed pages: `build-ideas`, `demand-signals`,
  `revenue-proof`, and `launches` on the `build` page — in that order
  (Ideas / Asks / Proof / Launches); `shipped` on the `code` page, after
  `custom-trending`; `developing` on the Today page, first among today's
  extra sections.
- `metrics` and `tags` are optional arrays; omit them rather than leaving
  empty placeholders.
- `isNew: true` marks an item that did not appear in the previous day's brief
  (matched by URL, falling back to title); the app renders a "new" badge.
  `scripts/create_morning_brief.py` computes this automatically against the
  most recent earlier day file — omit the field rather than setting `false`.
- `previously` lists earlier brief days an item appeared on (same URL, falling
  back to title), newest first, looking back up to 5 day files. It is computed
  by `scripts/create_morning_brief.py` — don't write it by hand. An item never
  carries both `previously` and `isNew` (`previously` wins); the app renders a
  "Day N" flag (N = `previously.length + 1`) in place of the new badge.
- The app renders every item in a section — there is no preview/"Show all"
  toggle. Control section length through the source caps in `config.toml`
  (`top_x_threads`, `top_github_projects`, `max_demand`, …), not in the app.
  The legacy `previewCount` field is ignored if present.
- Always update `index.json` when adding a day. Keep old day files — the site
  is the archive.
- `scripts/create_morning_brief.py` fetches sources and writes a valid day
  file with `headline`/`executiveSummary` left empty; the agent's job is to
  fill those in (and improve item `body` prose) before committing.
- Re-running the script for an existing day preserves the agent's
  `headline`, `executiveSummary`, and `followUps`. It also preserves the
  `developing` and `build-ideas` sections wholesale when they look
  agent-authored (the existing section, matched by id, has items with
  non-empty bodies) — so a re-fetch never clobbers rewritten prose.
