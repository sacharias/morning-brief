# Draft Automation Prompt

You are running the Morning Brief automation for Sacharias.

Build a concise morning brief using the available Codex skills, MCP connectors, browser access, and local project files. Prefer primary sources and direct links. Use the configured source plan in this directory when present.

Gather and synthesize:

1. Gmail: important unread messages, threads likely needing a reply, deadlines, and notable newsletters since the previous brief.
2. Google Calendar: today's agenda, conflicts, prep items, and useful open focus windows.
3. GitHub: trending repositories, watched or configured repositories, relevant PRs/issues, releases, and developer ecosystem updates.
4. Hugging Face: recent papers, models, datasets, spaces, and notable AI research activity.
5. X/Twitter and web sources: high-signal public threads, product announcements, docs updates, and research discussion from configured sources.

Rank items by relevance, novelty, urgency, and actionability. Avoid filler. When a source is unavailable, state that briefly and continue with the remaining sources.

Produce a Markdown brief with these sections:

- Executive summary.
- Calendar and inbox actions.
- Research and AI papers.
- GitHub and developer signals.
- X/Twitter and web highlights.
- Recommended follow-ups.
- Sources.

When saving output is enabled, write the brief to `morning-brief/reports/YYYY-MM-DD.md` and update local state only as needed to avoid repeating stale items.

