#!/usr/bin/env bash
# job-hunter family — one-shot installer for macOS / Linux
#
# Installs all 6 family skills (orchestrator + 5 members) into each supported
# agent-harness skills directory:
#   ~/.claude/skills/<member>/     (Claude Code)
#   ~/.agents/skills/<member>/     (OpenAI Codex AND OpenClaw — shared path)
#   ~/.hermes/skills/<member>/     (Hermes Agent)
#
# Members: job-hunter (orchestrator), career-profile, job-search,
#          resume-tailor, application-tracker, outcome-learning.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/wexxwuther/job-hunter/main/install/install.sh | bash
# Or, after cloning:
#   ./install/install.sh

set -euo pipefail

REPO="wexxwuther/job-hunter"
BRANCH="main"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

MEMBERS=(job-hunter career-profile job-search resume-tailor application-tracker outcome-learning)
HARNESS_ROOTS=(".claude/skills" ".agents/skills" ".hermes/skills")

echo "==> Downloading job-hunter family (branch: $BRANCH)..."
if command -v git >/dev/null 2>&1; then
  git clone --depth=1 --branch "$BRANCH" "https://github.com/$REPO.git" "$TMPDIR/src"
else
  if ! command -v curl >/dev/null 2>&1; then
    echo "ERROR: need either git or curl on PATH" >&2
    exit 1
  fi
  curl -fsSL "https://github.com/$REPO/archive/refs/heads/$BRANCH.tar.gz" | tar -xz -C "$TMPDIR"
  mv "$TMPDIR/job-hunter-$BRANCH" "$TMPDIR/src"
fi

# Install each member into each harness root. Strip developer-only dirs from
# each installed member copy (tests, docs/superpowers, any __pycache__).
for member in "${MEMBERS[@]}"; do
  SRC="$TMPDIR/src/$member"
  if [ ! -d "$SRC" ]; then
    echo "WARNING: family member '$member' not found in repo; skipping." >&2
    continue
  fi
  for root in "${HARNESS_ROOTS[@]}"; do
    DEST="$HOME/$root/$member"
    echo "==> Installing $member -> $DEST"
    mkdir -p "$(dirname "$DEST")"
    rm -rf "$DEST"
    cp -R "$SRC" "$DEST"
    rm -rf "$DEST/tests" "$DEST/docs/superpowers"
    find "$DEST" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
  done
done

echo ""
echo "Done. Installed the job-hunter family (6 skills) to ~/.claude, ~/.agents (Codex+OpenClaw), and ~/.hermes."
echo "Restart your agent and try:"
echo "  \"Help me run my whole job search.\"   (orchestrator routes to the right members)"
echo "  \"Just tighten my resume.\"            (routes straight to resume-tailor)"
