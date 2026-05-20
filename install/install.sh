#!/usr/bin/env bash
# job-hunter — one-shot installer for macOS / Linux
# Installs the skill into all four supported agent paths:
#   ~/.claude/skills/job-hunter/      (Claude Code)
#   ~/.codex/skills/job-hunter/       (OpenAI Codex)
#   ~/.openclaw/skills/job-hunter/    (OpenClaw)
#   ~/.hermes/skills/job-hunter/      (Hermes Agent)
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/wexxwuther/job-hunter/main/install/install.sh | bash
#
# Or, after cloning:
#   ./install/install.sh

set -euo pipefail

REPO="wexxwuther/job-hunter"
BRANCH="main"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

echo "==> Downloading job-hunter (branch: $BRANCH)..."
if command -v git >/dev/null 2>&1; then
  git clone --depth=1 --branch "$BRANCH" "https://github.com/$REPO.git" "$TMPDIR/job-hunter"
else
  if ! command -v curl >/dev/null 2>&1; then
    echo "ERROR: need either git or curl on PATH" >&2
    exit 1
  fi
  curl -fsSL "https://github.com/$REPO/archive/refs/heads/$BRANCH.tar.gz" \
    | tar -xz -C "$TMPDIR"
  mv "$TMPDIR/job-hunter-$BRANCH" "$TMPDIR/job-hunter"
fi

# Strip git history and developer-only files before install
rm -rf "$TMPDIR/job-hunter/.git" \
       "$TMPDIR/job-hunter/.github" \
       "$TMPDIR/job-hunter/install"

DESTS=(
  "$HOME/.claude/skills/job-hunter"
  "$HOME/.codex/skills/job-hunter"
  "$HOME/.openclaw/skills/job-hunter"
  "$HOME/.hermes/skills/job-hunter"
)

for DEST in "${DESTS[@]}"; do
  echo "==> Installing to $DEST"
  mkdir -p "$(dirname "$DEST")"
  rm -rf "$DEST"
  cp -R "$TMPDIR/job-hunter" "$DEST"
done

echo ""
echo "Done. Restart your agent and try:"
echo "  \"Find me senior backend jobs in Seattle, \$180k+, that aren't ghost listings.\""
