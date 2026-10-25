# local-runs-and-estimates
Objective: estimate the processing time of the proof of concept and the full experiments from a short local measurement, monitor the local environment (micromamba, target venvs, required libraries, device), and tell the operator which run options exist — local, Kaggle, Colab — for each stage, with readiness and estimates.
Branch: feat/local-runs-and-estimates · Delivery: single merge · Runners: `npm run test:py`, `npm test`.

## Specs

- S1 (estimate in the phases): "ajusta tambien la prueba de concepto y el experimento completo en sus fases, para que se incluya una estimacion del tiempo de proceso, de manera local".
- S2 (local runs monitored): "que se consideren en el panel de experimientos corridas locales, monitoreando librerias requeridas, microbamba o lo que se requiera, y si se tienen instaladas o no".
- S3 (run options): "que se le informe al usuario posibles opcioes de corrida, desde local, kaggle y colab (si disponibles), para monitorear opciones de rpuebas de concepto y pruebas experimentos completos".

## Shared conventions (all units follow; report a conflict instead of diverging)

- **Timing record**: `<target>/<Name>/Results/timing.json`, written by a short timing probe (one epoch of one fold per arm) BEFORE the pilot and before the full run:
  `{"schema": 1, "measurements": [{"measuredAt": "<ISO-8601>", "host": "local" | "kaggle:<owner>" | "colab:<owner>", "device": "cpu" | "mps" | "cuda:<gpu name>", "arm": "<arm id>", "unit": "epoch", "secondsPerUnit": <float>, "unitsMeasured": <int>, "setupSeconds": <float, optional>}], "scales": {"poc": {"arms": <int>, "folds": <int>, "seeds": <int>, "epochs": <int>}, "full": {"arms": <int>, "folds": <int>, "seeds": <int>, "epochs": <int>}}}`.
  `scales` is copied by the agent from the approved protocol (experiments revision) and the declared pilot; nothing guesses it.
- **Estimate formula** (one definition; both units implement exactly this): for a stage `s` and a host `h` with measurements, `seconds = mean(secondsPerUnit over h's measurements, per arm when available else overall) × epochs_s × folds_s × seeds_s × arms_s + setupSeconds_h × folds_s × seeds_s` (setup 0 when absent). Report it as a range ±20% (stated as "±20%, single-probe extrapolation"), never as a point claim. A host with no measurement reads `unmeasured` — remote hosts are never estimated from local timings scaled by a guessed factor.
- **Run options**: per stage (`poc`, `full`) one row per host family — `local`, `kaggle`, `colab` — with `available` (local: workspace env or target venv present and required libraries installed; kaggle: token active, official CLI installed, ≥1 validated worker account; colab: official CLI installed and ≥1 team owner signed in, and for `full` ≥1 owner on a paid tier), `estimate` (formula above or `unmeasured`), and a one-line reason.

## Tasks

- T1 [S1] remote-parallelism `estimate` verb + "Estimate before you scale" doctrine in proposal-implementation and experimental-implementation + walk/build agents run it — route: delegated (parallel units) — done
- T2 [S2,S3] dashboard: local environment table, run-options table, Fase 5 estimate step — route: delegated (parallel units) — done
- T3 shared pins, projections, suite, merge, push, QMLEEG upgrade, restart dashboards — route: inline — done

## Log

- L1 (2026-10-25, user verbatim): "ajusta tambien la prueba de concepto y el experimento completo en sus fases, para que se incluya una estimacion del tiempo de proceso, de manera local, y que se consideren en el panel de experimientos corridas locales, monitoreando librerias requeridas, microbamba o lo que se requiera, y si se tienen instaladas o no, y que se le informe al usuario posibles opcioes de corrida, desde local, kaggle y colab (si disponibles), para monitorear opciones de rpuebas de concepto y pruebas experimentos completos"
- L2 Verification: T1 195 passed, T2 130 passed; full suite 6875 passed with the 2 known environment failures; node 784/784. Released with Colab team accounts as 0.22.0.
