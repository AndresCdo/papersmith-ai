# WSL initialization and command center
Objective: Make the authorized WSL initialization/browser flow work safely in Smith's base repository. Branch: `fix/wsl-init-command-center`. Delivery strategy: single reviewable feature branch; release publication excluded.
Runner: `.venv/bin/python -m pytest` (focused suites first); verify from Ubuntu on WSL2 and Windows HTTP bridge.

## Specs
S1. “smith ui no esta levantando” and “luego levanta tablero”: verify server and Windows-accessible URL; fix WSL browser opening without regressing other hosts.
S2. “revisa los problemas que estamos teniendo para init y levantar en windows con wsl, ajustalos, verifia  que esten bien”: reproduce the existing init refusal and add a safe opt-in only as selected below.
S3. “Opción explícita de importar archivos existentes”: preserve original files with no overwrites while allowing init into an existing nonempty directory when explicitly requested; default refusal remains unchanged.
S4. “haz comit  y mergea en proyecto base smith y dale push para realease con actualizacion y pruebas en windows con wsl”: work-unit commits, merge into the base project and push after applicable checks.
S5. “Sólo merge y push de commits”: do not create a release tag, GitHub Release or PyPI publication.

## Tasks
T1 (S2-S3): delegated writer + verifier; done; RED CLI unknown flag, GREEN 36 passed; commit 475f1256 — opt-in import, tests, CLI/help/docs.
T2 (S1-S2): delegated writer + verifier; done; GREEN 26 passed and live WSL browser launch requested; commit 892fc7e0 — WSL browser launcher, tests/docs.
T3 (S2): delegated writer + verifier; done; GREEN 49 passed; commit a3d37377 — carry forward Pi web-tool mapping fix into base Smith, with tests.
T4 (S4-S5): inline; in progress; commit pending — integration verification, version/update notes as needed, merge and push only.
T5 (S4-S5): inline; done — user authorized and only 20 tracked `.pi/agents` sync edits were restored; pre-existing untracked files untouched.

## Log
L1 (user, verbatim): smith ui no esta levantando, revisa los problemas que estamos teniendo para init y levantar en windows con wsl, ajustalos, verifia  que esten bien, luego levanta tablero,  y haz comit  y mergea en proyecto base smith y dale push para realease con actualizacion y pruebas en windows con wsl
L2 (user decision, verbatim): Opción explícita de importar archivos existentes
L3 (user decision, verbatim): Sólo merge y push de commits
L4: The current `smith ui . --no-browser --no-terminal` serves HTTP 200 on WSL localhost:8080, but Python `webbrowser` reports no registered handler. The prior `smith init .` refused the nonempty destination before writing, by design. The existing base repo had untracked `.antigravity/` and `odd/tasks/local-installation.md`; do not touch them. Windows native tests are not established; WSL2 and Windows PowerShell HTTP bridge are available.
L5: Engram rejected the cross-project mirror because this server lacks `capabilities.isolated_session_registration`; mirror pending. The local document remains authoritative for this feature.
L6: T1 RED unknown CLI flag; GREEN 36 passed after parent-symlink race correction; independent verifier PASS with best-effort concurrent rollback limitation. T2 GREEN 26 passed and independent verifier PASS; Windows PowerShell fetched dashboard HTTP 200 and WSL requested Windows browser. T3 GREEN 49 passed; independent verifier PASS for mapping, Pi runtime availability requires extension. First T1 commit failed exit 128 because Git author identity was unset; user supplied an identity, local repo configuration was set, then T1 committed as 475f1256. T2 committed 892fc7e0 and T3 committed a3d37377. Engram cross-project mirror still pending.
L7: RDD is on; native assessment could not classify this committed range because unrelated untracked paths need declaration. Provider inspect initially stopped on stale managed assets; its exact `gentle-ai sync --agent pi` continuation modified 20 tracked `.pi/agents` files and global Pi settings outside this feature. No incidental changes were staged. Inspect then offered a workspace-change candidate containing only incidental agent modifications, not feature commits. User authorized restoration; exact 20 tracked sync modifications were restored with Git, leaving unrelated untracked files untouched. Native candidate remains unresolved. Full suite pending.
L8: `origin/main` and the peeled remote tag `v0.19.1^{}` both point at 4912125e; release policy requires a new version for shipped source changes. Only merge and push commits were authorized; no tag or GitHub/PyPI publication. `upstream/main` tracks the same base, while `origin` is the configured push remote (fork). No merge or push yet.
