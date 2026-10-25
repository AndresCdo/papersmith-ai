---
name: backlog-steward
description: Review, group and resolve papersmith's GitHub issues and PRs by root cause. Trigger: triage, backlog, issue flood, review PRs, close issues, resolve issues, audit remediation. Repository-only maintainer skill; never shipped to workspaces.
---

# Backlog steward

Papersmith's issues arrive in floods (one audit filed 35 at once). Handling them
one by one produces N patches for one cause, closures nobody can verify, and PRs
that cross each other. This skill groups the backlog by **root**, resolves one
root per PR, and closes an issue only against evidence.

Adapted from gentle-ai's `systemic-issue-triage`, `issue-root-resolution`,
`branch-pr` and `judgment-day`. What papersmith adds: the grouping is a versioned
data file that a script checks against live GitHub, not a hand-kept meta-issue
that drifts.

## Tools

| Command | Does |
|---|---|
| `python3 maintainer/backlog.py snapshot <file>` | Freezes the open issues and PRs (needs `gh`) |
| `python3 maintainer/backlog.py stale [--snapshot f]` | Lists issues whose cited files or lines no longer exist. A hint, never a verdict |
| `python3 maintainer/backlog.py check [--snapshot f]` | Exits 1 unless every open issue sits in exactly one root, every listed issue is open, and every open PR links issues of a single root |
| `python3 maintainer/backlog.py render [--snapshot f]` | Prints the tracker issue body |
| `python3 maintainer/backlog.py pr-link --body-env PR_BODY` | The CI gate: a PR body must carry `Closes/Fixes/Resolves/Refs #N` |

The root map is `maintainer/backlog/roots.json`:

```json
{"pinned_commit": "<sha triaged against>",
 "roots": [{"key": "ci-env", "title": "...", "tier": 1, "state": "open",
            "fix": "one sentence: the single change that closes every issue below",
            "proof": "the test or CI run that shows it", "issues": [108],
            "evidence": {"108": "path:line on the pinned commit"}}]}
```

Tiers: **0** close now (already fixed, code gone, duplicate); **1** blocks CI or
releases; **2** a contained defect with a known fix; **3** needs a maintainer
decision before code (design, refactor, policy, feature).

## 1. Triage: every issue gets exactly one bucket

Pin a commit and read each issue body in full. A large backlog goes to read-only
explorers, about 15 issues each, using a shared root vocabulary.

| Bucket | Meaning | Goes to |
|---|---|---|
| A | Real, still present on the pinned commit | Its root (tier 1–2) |
| B | Duplicate of #M | #M's root, noting the duplicate |
| C | Already fixed, or the code is gone | Tier 0, with the proving commit or line |
| D | Design, large refactor, policy or feature | Tier 3 |
| E | Unclear | Ask the reporter one question, tier 3 |

Rules:

- **The stated mechanism is a hypothesis.** Only the symptom is evidence. Check
  it against current code: audit line numbers go stale (`backlog.py stale`
  helps).
- **N issues never justify N patches.** Issues that share a cause share a root
  and one fix.
- **One thread, two failure modes:** split the thread, or leave it open. Never
  close half of it.
- Finish with `backlog.py check` green, then publish `render` as the tracker
  issue. Update it after each root closes.

## 2. Resolve: one root, one branch, one PR

1. Branch `fix/<root-key>` from a **green** `main`. Restoring red CI is
   always tier 1, root zero: nothing else can be accepted while CI cannot tell
   good from bad.
2. **Reproduce first.** Write the failing test through the public interface
   and watch it go RED on unmodified `main`. If it passes there, the diagnosis is
   wrong even if the report is right. Go back to the symptom.
3. Rank fix shapes:
   - (a) delete the mechanism so the class cannot recur;
   - (b) add a guard test that fails when the shape returns;
   - (c) make a local fix behind the repro.
   If a fix adds a state, flag, verb or a second copy of existing data, redesign
   it first.
4. Keep tests and docs in the same commit as the behavior, under Conventional
   Commits. A root over about 400 changed lines is split into stacked PRs, or
   carries `size:exception` with a stated reason.
5. The PR body names the root, carries `Closes #N` for every issue it resolves
   (`Refs #N` for a partial step), and records RED → GREEN with the test names.

## 3. Accept a PR (own or external)

A PR is accepted only when all of these hold:

1. **It links issues of a single root** (`backlog.py check`; CI enforces the
   link). A PR that spans roots is split or narrowed.
2. **CI ran and is green on the PR head, rebased on current `main`.** Fork
   PRs wait for a maintainer to approve their workflow run (`action_required`);
   approve it after reading the diff, never before.
3. **The repro is real.** Re-run the PR's named RED test against `main` without
   the fix. It must fail there and pass with the fix.
4. **Bounded dual review.** Two blind, read-only reviewers (for example the
   `jd-judge-a`/`jd-judge-b` agents, or two fresh reviewers) get the same frozen
   diff and the linked issues, and nothing about each other.
   - A finding counts only when both confirm it, or when it reproduces
     deterministically.
   - At most two fix rounds, each re-reviewed on the fix diff only. Then the
     verdict is APPROVED, or ESCALATED to a human with the open findings.
   - A verdict informs the merge decision; it never replaces the operator's.
5. **Merging, closing and commenting are operator decisions.** The agent
   prepares the batch (merge order, closure comments, tracker update) and asks
   once.

## 4. Close an issue: only with evidence

An issue closes for exactly one of these reasons, stated in a closing comment:

| Reason | Comment must cite |
|---|---|
| Fixed | The merge commit and the named test that went RED → GREEN |
| Already fixed | The commit or current `path:line` that shows it, plus a test if one exists |
| Code gone | The commit that removed the code |
| Duplicate | The canonical issue |
| Superseded | The recorded maintainer decision |

If in doubt, leave it on a borderline list in the tracker. Do not close it.
After closing, remove the issue from `roots.json` (or move the root's `state` to
`closed`) and re-run `check`.

## Do not

- Ship maintainer tooling under `skills/` or `.claude/agents/`. Both reach every
  workspace through `KIT_ENTRIES`. This kit lives in `maintainer/`.
- Close an issue because a PR "should" fix it, or because an agent said so.
- Merge with red or absent CI. A red `main` is fixed first.
- Treat a reviewer verdict as merge authority.
