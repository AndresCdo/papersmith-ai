#!/usr/bin/env bash
#
# Cross-harness wiring smoke: init produces a workspace four harnesses
# (claude, opencode, pi, antigravity) must actually be able to reach into.
# This asserts the specific files and links that make that true, which
# neither cli-paper-smoke.sh nor cli-paper-live-smoke.sh checks:
#
#   1. .claude/skills, .opencode/skills, .pi/skills and
#      .agents/skills are relative symlinks that resolve to the workspace's own skills/.
#   2. Every .claude/agents/*.md's referenced .claude/skills/<name>/SKILL.md
#      resolves both canonically and through every harness's own symlink.
#   3. The agent roster in CLAUDE.md/OPENCODE.md/PI.md/.agents/AGENTS.md
#      matches the real .claude/agents/*.md files.
#   4. .claude/commands/, .opencode/commands/ and .pi/prompts/ list the same
#      filenames as each other and as skills/'s top-level SKILL.md directories.
#   5. upgrade repairs a broken harness symlink live, and never destroys
#      real (non-symlinked) content sitting at the same path.
#
# Hermetic: no npm, no network, same tier as cli-paper-smoke.sh (not the
# live one).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WS="${1:-$(mktemp -d)}"
if [[ -z "${1:-}" ]]; then trap 'rm -rf "$WS"' EXIT; fi
export PYTHONPATH="$ROOT/src"
PY="$ROOT/.venv/bin/python"

fail() {
  echo "wiring smoke: FAIL (check $1): $2" >&2
  exit 1
}

# `--no-env` is what keeps this hermetic: `init` provisions a multi-gigabyte
# micromamba environment by default, and no offline smoke may do that.
"$PY" -m papersmith.cli init "$WS" --tools claude,opencode,pi,antigravity --no-npm --no-env --remote local

CANONICAL="$WS/skills"
CANONICAL_RESOLVED="$(readlink -f "$CANONICAL")"

# Check 1: harness skill symlinks exist, are relative, and resolve to skills/.
for link in .claude/skills .opencode/skills .pi/skills .agents/skills; do
  path="$WS/$link"
  test -L "$path" || fail 1 "$link is not a symlink"
  target="$(readlink "$path")"
  [[ "$target" != /* ]] || fail 1 "$link symlink target is absolute: $target"
  [[ "$(readlink -f "$path")" == "$CANONICAL_RESOLVED" ]] \
    || fail 1 "$link does not resolve to $CANONICAL_RESOLVED"
done

# Check 2: every agent's referenced skill resolves canonically and through
# every harness prefix (label-agnostic: grep the literal path substring,
# don't assume the "Skill:" introduction).
for agent in "$WS"/.claude/agents/*.md; do
  line="$(grep -m1 '\.claude/skills/' "$agent" || true)"
  [[ -n "$line" ]] || fail 2 "$(basename "$agent") has no .claude/skills/ reference"
  name="$(printf '%s\n' "$line" | sed -E 's#.*\.claude/skills/([^/]+)/SKILL\.md.*#\1#')"
  [[ -n "$name" && "$name" != "$line" ]] \
    || fail 2 "could not extract skill name from $(basename "$agent"): $line"
  test -f "$WS/skills/$name/SKILL.md" \
    || fail 2 "skills/$name/SKILL.md missing (referenced by $(basename "$agent"))"
  for prefix in .opencode .pi .agents; do
    test -f "$WS/$prefix/skills/$name/SKILL.md" \
      || fail 2 "$prefix/skills/$name/SKILL.md missing (referenced by $(basename "$agent"))"
  done
done

# Check 3: agent roster parity across the four generated harness docs.
agent_names="$(cd "$WS/.claude/agents" && ls -- *.md | sed 's/\.md$//' | sort)"
for doc in CLAUDE.md OPENCODE.md PI.md .agents/AGENTS.md; do
  doc_names="$(grep -oE '^- `[^`]+`' "$WS/$doc" | sed -E 's/^- `([^`]+)`$/\1/' | sort || true)"
  [[ "$doc_names" == "$agent_names" ]] \
    || fail 3 "$doc agent roster does not match .claude/agents/*.md"
done

# Check 4: slash-command parity between the three harness dirs and skills/.
claude_cmds="$(cd "$WS/.claude/commands" && ls -- *.md | sort)"
opencode_cmds="$(cd "$WS/.opencode/commands" && ls -- *.md | sort)"
pi_cmds="$(cd "$WS/.pi/prompts" && ls -- *.md | sort)"
[[ "$claude_cmds" == "$opencode_cmds" ]] \
  || fail 4 ".claude/commands and .opencode/commands list different filenames"
[[ "$claude_cmds" == "$pi_cmds" ]] \
  || fail 4 ".claude/commands and .pi/prompts list different filenames"
skill_cmds="$(cd "$WS/skills" && for d in */; do
  d="${d%/}"
  [[ "$d" == "_core" ]] && continue
  [[ -f "$d/SKILL.md" ]] && echo "$d.md"
done | sort)"
[[ "$claude_cmds" == "$skill_cmds" ]] \
  || fail 4 "command filenames do not equal skills/ top-level SKILL.md directories"

# Check 5: upgrade repairs a broken harness symlink, and never destroys real
# (non-symlinked) content sitting at the same path.
DECOY="$WS/.papersmith-wiring-smoke-decoy"
mkdir -p "$DECOY"
ln -sfn "$DECOY" "$WS/.claude/skills"
"$PY" -m papersmith.cli upgrade "$WS"
[[ "$(readlink -f "$WS/.claude/skills")" == "$CANONICAL_RESOLVED" ]] \
  || fail 5 "upgrade did not repair .claude/skills back to skills/"

rm "$WS/.opencode/skills"
mkdir -p "$WS/.opencode/skills"
echo "real content" > "$WS/.opencode/skills/sentinel.txt"
"$PY" -m papersmith.cli upgrade "$WS"
if test -L "$WS/.opencode/skills"; then
  fail 5 "upgrade replaced real .opencode/skills content with a symlink"
fi
test -f "$WS/.opencode/skills/sentinel.txt" \
  || fail 5 "upgrade destroyed real content at .opencode/skills/sentinel.txt"

echo "wiring smoke: ok ($WS)"
