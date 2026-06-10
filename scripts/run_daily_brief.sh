#!/bin/zsh
# Daily Morning Brief runner — invoked by launchd/cron.
# Runs the fetch scripts and has Codex write the editorial layer, then commits & pushes.
set -euo pipefail

# cron/launchd start with a minimal environment, so set PATH explicitly.
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"

PROJECT_DIR="/Users/sacharias/codex-automations/morning-brief"
cd "$PROJECT_DIR"

LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"
STAMP="$(date +%Y-%m-%d_%H%M%S)"
LOG="$LOG_DIR/brief_$STAMP.log"

{
  echo "=== Morning Brief run started: $(date) ==="

  # Hand the whole job to Codex non-interactively. It runs `npm run brief`, fills
  # in the editorial layer per automation-prompt.md, validates, commits, and pushes.
  #
  # --dangerously-bypass-approvals-and-sandbox: unattended run needs network
  #   (curl, ClickHouse, Chrome for X) and `git push`, which the sandbox blocks.
  # -C: working root.   -o: capture the agent's final message.
  codex exec \
    --dangerously-bypass-approvals-and-sandbox \
    -C "$PROJECT_DIR" \
    -o "$LOG_DIR/last_message_$STAMP.txt" \
    "$(cat automation-prompt.md)

Run the full update now: fetch all sources, write the headline/executiveSummary/item bodies/followUps, validate the JSON, then commit and push the changed files under public/data/ to main. Work autonomously without asking for confirmation."

  echo "=== Morning Brief run finished: $(date) ==="
} >> "$LOG" 2>&1
