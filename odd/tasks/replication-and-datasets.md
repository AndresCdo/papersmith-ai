# replication-and-datasets
Objective: a `paper-replicator` agent that reimplements a paper's method without public code, and a `datasets` skill (toy sets always, discovery, quality checks, official preparation, private Kaggle publishing with consent), both running on the active harness subscription and compatible with Claude Code, OpenCode and Pi.
Branch: feat/replication-and-datasets · Delivery: single merge (user asked to merge and push) · Runners: `npm run test:py`, `npm test`.

## Specs

- S1 (replicator agent): "para replicar el paper, implementalo en paper smith como lo recomiendas, pero crea un agente en el proyecto para eso. asegurate de que use la subscripcion activa, y que sea compatibel con claude code, opencode y pi". Recommended method: from the `paper-ingestion` Markdown, plan → analyze → code; read the cited papers that matter ("lineage"); every hyperparameter cites its section or equation or is marked unspecified; verify with invariant tests and a short run on the toy set before GPU. No external LLM API, no API key, no DeepCode dependency: it runs as a harness subagent on the session's own model.
- S2 (datasets skill): "construye la skiil de dataset con el diseño propuesto, recuerda asegurar que sea compatible con claude code, opencode y pi". Design (from the prior turn): toy set always for the proof of concept (seeded synthetic data); search official paper repositories, Kaggle, Hugging Face, OpenNeuro, Zenodo (Google Dataset Search has no API: manual link only); quality checks recorded as JSON; one versioned official preparation (splits by subject) shared by proof of concept and full experiments; publish to Kaggle as a private dataset via `kaggle datasets create` / `version -m`, with human gates: source license check (refuse NC/ND/credentialed unless overridden), explicit upload consent per dataset, separate consent before making it public. Agents: `dataset-scout` (search + license) and `dataset-curator` (QC, preparation, publishing).
- S3 (delivery): "realiza las pruebas, comit y megrea y push en proyecto base paper smith, y actualiza proyecto qmleeg".

## Tasks

- T1 [S1] `paper-replicator` agent + proposal-implementation delegation — route: delegated (parallel units, disjoint surfaces) — done (RED 9 failed → GREEN; stretch fidelity)
- T2 [S2] `datasets` skill + `dataset-scout` / `dataset-curator` agents + panel datasets section — route: delegated (parallel units, disjoint surfaces) — done (RED collection error → GREEN 69 passed)
- T3 [S3] shared pins, projections, full suite, verifier, merge, push, QMLEEG upgrade — route: inline — done

## Log

- L1 (2026-10-24, user verbatim): "para replicar el paper, implementalo en paper smith como lo recomiendas, pero crea un agente en el proyecto para eso. asegurate de que use la subscripcion activa, y que sea compatibel con claude code, opencode y pi. y y construye la skiil de dataset con el diseño propuesto, recuerda asegurar que sea compatible con claude code, opencode y pi. realiza las pruebas, comit y megrea y push en proyecto base paper smith, y actualiza proyecto qmleeg"
- L2 Evidence: DeepCode is MIT and free but bills the user's own LLM API key, so it is excluded by S1; the live Kaggle MCP lists `upload_dataset_file`, `update_dataset_metadata`, `get_dataset_status` and no `create_dataset` unauthenticated, so creation goes through `kaggle datasets create` (private unless `-u`); `kaggle datasets version` requires `-m`.
- L3 Verification: independent verifier PASS S1; S2 blocker (publish copied symlinked/outside files into the upload folder) fixed with `upload_source` containment + 3 regression tests; advisories fixed: spelled-out CC attribution license, uneven-subject fold balance (deviation-increase cost), publishing with no data file refused, search listing sorted by mtime. Full suite 6659 passed, 3 known failures (case-insensitive FS, version bump, smoke fastapi); node 784/784; projections clean (116 files).
