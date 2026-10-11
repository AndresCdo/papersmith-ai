# Release 0.13.0, the red main it inherits, and the LIAUNAL sync

Objective: leave `main` green, sync the clone with the LIAUNAL organization, and
cut release 0.13.0 with its tag, its notes and its pinned example — leaving the
first PyPI publication as the human step it is.

Authorized scope: `.github/workflows/publish.yml`, `CHANGELOG.md`, `README.md`,
`odd/tasks/release-0.13.0.md`, and the Git/tag/release operations themselves.
No change under `src/`, `skills/` or `scripts/`.

## What was measured before touching anything

`main` at `55dcb4e` is red. Three consecutive CI runs failed on 2026-10-08
(`37774645144`, `37800362139`, `37804140868`). The Node job passes; Python Test
Suite fails inside `scripts/clean_context_gate.py`:

```
FAIL: the gate does not pass on a machine with no personal context:
  FAILED tests/test_papersmith_init.py::SuiteStaysOfflineTests
         ::test_every_cli_init_in_the_suite_skips_provisioning
```

Reproduced locally, exact offender named:

```
these test-suite `init` invocations skip the npm step and not the environment
step, so each one performs a multi-gigabyte network install and leaks it into
the temp dir: .github/workflows/publish.yml:71
```

`invocations_outside_the_suite()` anchors on `--no-npm` and requires `--no-env`
in a **forward** window of 120 characters. `publish.yml:71` writes
`init /tmp/probe-ws --no-env --no-npm`, so the required flag sits behind the
anchor and is never seen.

Every other caller in the repository writes `--no-npm --no-env`:
`tests/test_harness_matrix.py` (three), `tests/opencode-plugin.test.mjs`,
`tests/pi-extension.test.mjs`, `tests/workspace_series.py`. `publish.yml:71` is
the only line in the repository that reverses them.

## Decisions

**Fix the workflow, not the guard.** The guard encodes the convention the whole
repository already follows, and swapping two flags restores it. Making the guard
order-insensitive is the more durable fix and is recorded below as a follow-up
rather than taken here, because widening a guard that currently has teeth is a
separate change that deserves its own review.

**The release is a draft.** `publish.yml` triggers on `release: [published]`.
The Trusted Publisher on pypi.org is not configured (`https://pypi.org/pypi/papersmith-ai/json`
answers 404, so nothing has ever been published), and a published release would
fire a job that can only fail. A draft pushes the tag and creates the release
without triggering the workflow, so the first publication happens on the human
step, once, against a configured publisher — which is exactly what
`docs/releasing.md` asks for.

**The changelog section is completed.** `## 0.13.0` was written by `0b7e73a`
before `feat/upgrade-project-command`, `feat/pypi-publishing`,
`chore/liaunal-urls` and `docs/node-requirement-and-pypi-release` landed, so it
did not mention them. The release body is copied from that section, and notes
that omit the cycle's headline are a defect of the release rather than of the
work.

**The "no plain `pip install papersmith-ai`" paragraph in the manual stays.** It
is still true: a draft release publishes nothing. `docs/releasing.md` assigns
that edit to the release commit that first publishes.

**The `papersmith-ai-upstream` clone is left alone** (operator decision). Its
unmerged branches survive as `backup/*` tags, which are present on the LIAUNAL
remote.

## Tasks

- [ ] T1 — Fix `publish.yml:71` on `fix/init-offline-guard-flag-order`
- [ ] T2 — Guard and version tests green
- [ ] T3 — Merge into `main`, push, CI green
- [ ] T4 — Push the retroactive tags `v0.6.0` and `v0.7.1`
- [ ] T5 — `chore/release-0.13.0`: complete the changelog, move the README pin
- [ ] T6 — Merge `--no-ff`, tag `v0.13.0` on the merge commit, push main and tag
- [ ] T7 — Draft GitHub release, body from the changelog section
- [ ] T8 — Audit: tag invariant, install from the tag
- [ ] T9 — Close this record with its evidence

## Follow-ups (found, not taken)

- The `--no-npm`/`--no-env` window in `SuiteStaysOfflineTests.invocations_outside_the_suite`
  is order-sensitive. Flag order is not semantically meaningful, so the guard
  should match both orders or assert on the flags as a set.
- `test_the_mcp_init_tool_skips_provisioning_unless_asked` fails on macOS only:
  `tempfile.mkdtemp()` returns `/var/folders/...` and `Path.resolve()` expands it
  to `/private/var/...`, which trips `WORKSPACE_ESCAPE`. Environmental, not
  affected by this work.
- `v0.6.0` and `v0.7.1` were the only tags missing from the LIAUNAL remote.
