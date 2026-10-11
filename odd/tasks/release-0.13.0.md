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

- [x] T1 — Fix `publish.yml:71` on `fix/init-offline-guard-flag-order` (`ab7e42e`)
- [x] T2 — Guard and version tests green — RED first, with the guard naming its own
      offender, then `19 passed, 4 skipped`
- [x] T3 — Merge `5afea9f`, push `55dcb4e..5afea9f`
- [x] T4 — Push the retroactive tags `v0.6.0` and `v0.7.1`; the LIAUNAL remote now
      carries all fifteen
- [x] T5 — `chore/release-0.13.0` (`0b630fa`): the two missing changelog entries and
      the README pin moved to `v0.13.0`
- [x] T6 — Merge `1d7a02b`, tag object `4bbd6db` peeling to it, pushed
      `5afea9f..1d7a02b`
- [x] T7 — Draft release created (`isDraft: true`, `publishedAt: null`)
- [x] T8 — Audit: fifteen rows, every one `vX.Y.Z <commit> X.Y.Z 1`, plus an install
      from the tag
- [x] T9 — This record

## Evidence

The guard was RED before the change and named its own offender, which is the
strongest form this evidence takes:

```
AssertionError: these test-suite `init` invocations skip the npm step and not
  the environment step, so each one performs a multi-gigabyte network install
  and leaks it into the temp dir: .github/workflows/publish.yml:71
```

After the one-line change, the three suites that could see it are green
(`19 passed, 4 skipped`). The four skips are `BuiltArtifactsCarryTheKitTests`,
which need a `dist/` that only the workflow produces.

The draft decision is verified rather than assumed: `gh run list
--workflow=publish.yml` is empty, so creating the release triggered nothing, and
`gh release list` shows 0.13.0 as `Draft` with 0.12.0 still `Latest`.

The audit passes on all fifteen tags:

```
v0.6.0   52c905e  0.6.0    1     v0.12.0  f24dece  0.12.0   1
v0.7.0   30a40ea  0.7.0    1     v0.13.0  1d7a02b  0.13.0   1
v0.7.1   64ae0c0  0.7.1    1     (…every tag, in order)
```

And a tag that does not resolve to a working install is not a release, so:

```
$ pip install "papersmith-ai @ git+https://github.com/LIAUNAL/papersmith-ai@v0.13.0"
$ papersmith --version
papersmith 0.13.0
```

**Left open on purpose**: CI on `main` was still running when this record was
written. The prior failure was a single test inside the clean-context gate (the
log reads `1 failing test(s)`, the same one under the empty home and the decoy
home), so the gate's exit code is the thing to read when the run lands.

## Follow-ups (found, not taken)

- The `--no-npm`/`--no-env` window in `SuiteStaysOfflineTests.invocations_outside_the_suite`
  is order-sensitive. Flag order is not semantically meaningful, so the guard
  should match both orders or assert on the flags as a set.
- `test_the_mcp_init_tool_skips_provisioning_unless_asked` fails on macOS only:
  `tempfile.mkdtemp()` returns `/var/folders/...` and `Path.resolve()` expands it
  to `/private/var/...`, which trips `WORKSPACE_ESCAPE`. Environmental, not
  affected by this work.
- `v0.6.0` and `v0.7.1` were the only tags missing from the LIAUNAL remote.
