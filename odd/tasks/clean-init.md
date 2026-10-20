# Feature: a new smith workspace inherits nothing from older projects

Objective: everything `smith init` ships (the command center above all) shows only the new workspace's own data or neutral empty states; MONEEG content leaves the kit and stays reachable as a fixture.
Branch: `fix/clean-init-and-tutor-advisories` · Runner: `.venv/bin/python -m pytest`.

## Specs

- **S1** "de los pendientes, acepta y aplica el primero": polyglot uploads refused; a revision resolving outside the workspace is not this paper's; an invalid `model_spec.json` is not named as the source.
- **S2** "asegurate de que al inicar un proyecto nuevo con init de smith, no se arrasten artefactos ni graficas ni nada de proyectos antiguos": no MONEEG (or any other project's) data, numbers, names, paths or graphs in what the kit ships or in what the dashboard shows for a fresh workspace; neutral empty states instead; a guard test scans the kit and a fresh workspace's dashboard API for old-project markers.
- **S3** (assumption, preserves `moneeg_smith`): the MONEEG specification and novelty graph move to `tests/fixtures/moneeg/`, and a workspace may provide `.papersmith/novelty_graph.json` (as it already may `.papersmith/model_spec.json`).

## Tasks

| ID | Specs | Route | Status | Commit |
|----|-------|-------|--------|--------|
| T1 | S1 | inline | done | `1aec3569` |
| T2 | S2, S3 (model_spec, math_view, novelty_graph) | inline | pending | |
| T3 | S2 (server: flow, titles, canned messages) | inline | pending | |
| T4 | S2 (dashboard page) | inline | pending | |
| T5 | S2 (guard test, kit rebuild, fresh init check) | inline | pending | |

## Log

- **L1** (2026-10-20, user verbatim): "de los pendientes, acepta y aplica el primero, para el segundo, asegurate de que al inicar un proyecto nuevo con init de smith, no se arrasten artefactos ni graficas ni nada de proyectos antiguos,"
- **L2** Evidence: init.py and the kit are clean apart from `skills/_core/command_center/`: static MONEEG pillars/hypotheses/5-layer map/PoC in index.html, MONEEG data and `moneeg` branches in model_spec.py (and `get_model_specification(None)` returns MONEEG) and novelty_graph.py, canned MONEEG messages, titles and an absolute `/Users/...` flow path in server.py.
