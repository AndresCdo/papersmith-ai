#!/usr/bin/env bash
#
# setup-harnesses.sh — project the canonical `skills/` tree into every agent
# harness this repository supports.
#
# `skills/` at the repository root is the single source of truth. Each harness
# reads skills from its own convention directory, so this script links the
# canonical tree into each one. The links are relative and idempotent: re-running
# converges to the same layout without duplicating or nesting anything, and the
# checkout stays relocatable (an absolute link would keep pointing at wherever
# the checkout happened to live when the script last ran).
#
# Harnesses:
#   .claude/skills       Claude Code
#   .pi/skills           Pi
#   .opencode/skills     OpenCode
#   .agents/skills       Google Antigravity (skills invoked as /name)
#
# Usage:
#   npm run setup:harnesses
#   bash scripts/setup-harnesses.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CANONICAL="$ROOT/skills"

if [[ ! -d "$CANONICAL" ]]; then
  echo "error: canonical skills directory not found at $CANONICAL" >&2
  exit 1
fi

# harness-relative skill directory -> human label (order preserved)
HARNESSES=(
  ".claude/skills:Claude Code"
  ".pi/skills:Pi"
  ".opencode/skills:OpenCode"
  ".agents/skills:Antigravity"
)

# Preflight every destination before creating any directory or link. Existing
# directories have no ownership marker, so even an empty one belongs to the user.
for entry in "${HARNESSES[@]}"; do
  rel="${entry%%:*}"
  target="$ROOT/$rel"
  parent="$(dirname "$target")"

  if [[ -L "$parent" || ( -e "$parent" && ! -d "$parent" ) ]]; then
    echo "error: refusing harness parent $parent; move it aside manually and rerun setup." >&2
    exit 1
  fi

  if [[ -L "$target" ]]; then
    # Compare the direct link lexically, not through realpath: a foreign link
    # that eventually reaches skills/ is not a managed projection.
    destination="$(python3 -c 'import os,sys; p=sys.argv[1]; print(os.path.abspath(os.path.join(os.path.dirname(p), os.readlink(p))))' "$target")"
    if [[ "$destination" == "$CANONICAL" ]]; then
      continue
    fi
  elif [[ ! -e "$target" ]]; then
    continue
  fi

  echo "error: refusing unmanaged skills path $target; move it aside manually to preserve its contents and rerun setup." >&2
  exit 1
done

for entry in "${HARNESSES[@]}"; do
  rel="${entry%%:*}"
  label="${entry#*:}"
  target="$ROOT/$rel"

  # Correct managed links are already wired; preserve their spelling and inode.
  if [[ -L "$target" ]]; then
    printf 'already linked %-18s %s\n' "$label" "$rel"
    continue
  fi

  mkdir -p "$(dirname "$target")"

  # Relative link, computed rather than hardcoded so a harness nested deeper
  # than one level still resolves. python3 is already a hard repo dependency.
  link_target="$(python3 -c 'import os.path,sys; print(os.path.relpath(sys.argv[1], sys.argv[2]))' "$CANONICAL" "$(dirname "$target")")"

  ln -s "$link_target" "$target"
  printf 'linked %-18s %s -> %s\n' "$label" "$rel" "$link_target"
done

echo "Harness skill projection complete."
