#!/usr/bin/env python3
"""Custom GitHub trending from the public ClickHouse playground.

Queries the github_events dataset on play.clickhouse.com with our own
momentum algorithm: repos ranked by how much their star rate in the last
24 hours accelerated versus their average over the prior week. This
surfaces breakouts rather than already-popular repos, and the SQL is easy
to iterate on. Descriptions come from the unauthenticated GitHub API.
"""

from __future__ import annotations

import json
import subprocess
from concurrent.futures import ThreadPoolExecutor

CLICKHOUSE_URL = "https://play.clickhouse.com/?user=play"

QUERY = """
SELECT
  repo_name,
  countIf(created_at > now() - INTERVAL 1 DAY) AS stars_24h,
  round(countIf(created_at <= now() - INTERVAL 1 DAY) / 7, 1) AS baseline_per_day,
  round(stars_24h / greatest(baseline_per_day, 1), 1) AS acceleration
FROM github_events
WHERE event_type = 'WatchEvent' AND created_at > now() - INTERVAL 8 DAY
GROUP BY repo_name
HAVING stars_24h >= {min_stars}
ORDER BY acceleration DESC, stars_24h DESC
LIMIT {limit}
FORMAT JSON
"""


def curl(args: list[str], data: str | None = None, timeout: int = 60) -> str:
    command = ["curl", "--fail", "--silent", "--show-error", "--max-time", str(timeout), *args]
    if data is not None:
        command.extend(["--data-binary", data])
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return result.stdout


def repo_description(repo: str) -> str:
    try:
        raw = curl(
            [
                "--header", "Accept: application/vnd.github+json",
                "--header", "User-Agent: morning-brief/1.0",
                f"https://api.github.com/repos/{repo}",
            ],
            timeout=15,
        )
        return json.loads(raw).get("description") or ""
    except Exception:
        return ""


def fetch_custom_trending(limit: int = 50, min_stars: int = 8) -> list[dict]:
    raw = curl([CLICKHOUSE_URL], data=QUERY.format(limit=limit, min_stars=min_stars))
    rows = json.loads(raw)["data"]
    repos = [row["repo_name"] for row in rows]
    with ThreadPoolExecutor(max_workers=8) as pool:
        descriptions = list(pool.map(repo_description, repos))
    items = []
    for row, description in zip(rows, descriptions):
        repo = row["repo_name"]
        items.append(
            {
                "repo": repo,
                "url": f"https://github.com/{repo}",
                "description": description,
                "stars_24h": int(row["stars_24h"]),
                "baseline_per_day": float(row["baseline_per_day"]),
                "acceleration": float(row["acceleration"]),
            }
        )
    return items


def main() -> int:
    data = {"custom_trending": [], "access_notes": []}
    try:
        data["custom_trending"] = fetch_custom_trending()
    except Exception as error:
        data["access_notes"].append(f"Custom trending fetch failed: {error}")
    print(json.dumps(data, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
