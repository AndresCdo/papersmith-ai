# Feature: minimalist math panel, novelty card and Socratic math tutor

Objective: render the paper's mathematics as real LaTeX in a calm, card-based panel, condense the idea and novelty in a small card, and add a Socratic tutor that reads hand-written diagrams/maths and iterates with the user.
Branch: `feat/math-panel-tutor` · Delivery: ask-on-risk · Runners: `.venv/bin/python -m pytest`, `node --test`.

## Specs

- **S1** "revisa que efectivamente compile bien la matematica en latex": every equation the panel shows is LaTeX rendered by a real engine (KaTeX, vendored, offline) and a test proves each one compiles.
- **S2** "al poner la matematica asegurate de poner un panel minimalista, mas intuitivo y armonico, mira las librerias y formas de presentar https://ropero99.github.io/presentacion-piml/": cards (heading → display equation → one-line "Conexión"), a lema line, variables legend, `\underbrace` labels allowed; data comes from the workspace (proposal `$$…$$ \tag{N}` blocks, `.papersmith/model_spec.json`, MONEEG data as fallback), not hardcoded HTML.
- **S3** "debe existir un pequeño panel que resuma la novedad e idea central del paper o novedad desde el concepto con la matematica": a compact card with central idea, novelty, problem, contributions and the key equation.
- **S4** "debe permitir agregar o arrastrar imagenes escritas a mano que incluyan diagramas y la matematica iterando con el usuario": drag-and-drop / paste / pick images into the panel; they are stored in the workspace and shown in the thread.
- **S5** "crea un agente que analice e itere con la matematica, que entienda la imagen y pueda iterar en dicho panel, debe ser un tutor que ayude a entender y evalue el entendimiento de la matematica del usuario, usando metodo socratico y buscando justificar muy bien la novedad del articulo condensada en diagramas y matematicas": a `math-tutor` skill + agent (harness-native, projected to every runtime), run headless by the dashboard through the user's installed agent CLI (claude, fallback pi) with read-only tools, returning a structured turn (reply, Socratic question, LaTeX, understanding assessment).
- **S6** "explora e implementa la mejor alternativa": decision recorded in the Log.

## Tasks

| ID | Specs | Route | Status | Commit |
|----|-------|-------|--------|--------|
| T1 | S1, S2, S3 (data) | inline | done (RED import → 8 GREEN; KaTeX strict compile of every equation) | `532e7de4` |
| T2 | S1, S2, S3 (panel) | inline | done (merged into T5's commit) | `a68891c0` |
| T3 | S5 (skill + agent) | inline | done (contract suites green, rosters pinned) | `19099e39` |
| T4 | S4, S5 (backend: uploads, thread, headless runner) | inline | done (RED → 12 GREEN; live claude turn read the image) | `04cff4aa` |
| T5 | S4, S5 (tutor UI) | inline | done (live drop → claude turn in the browser) | `a68891c0` |
| T6 | all | independent verifier (risk item 2: runs an agent CLI, writes uploads) | in progress | |

## Log

- **L1** (2026-10-20, user request verbatim): "antes, vamos ha revisar el panel de mapa conceptual y que muestra la matematica, revisa que efectivamente compile bien la matematica en latex, al poner la matematica asgurate de poner un panel minimalista, mas intuitivo y armonico, mira las librerias y formas de presentar https://ropero99.github.io/presentacion-piml/, y agrega un panel para interactuar con la idea, debe exisitr en pequeño panel que resuma la novedad e idea central del paper o novedad desde el concepto con la matematica, y debe permitir agregar o arrastar imagenes escritas a mano que incluyan diagramas y la matematica iterando con el usuario. crea un agente que analice e itere con la matematica, que entienda la imagen y pueda iterar en dicho panel, debe ser un tutor que ayude a entender y evalue el entendienmiento de la matematica del usuario, usando metodo socratico y buscando justificar muy bien la novedad del articulo condensada en diagramas y matematicas, explora e implementa la mejor altenrativa al respecto"
- **L2** Evidence: no math engine is loaded; the visible equations are Unicode pseudo-math (several would render wrong as LaTeX); the 6 valid `latex` strings in `model_spec.py` are never shown; QMLEEG's `/api/model` is a placeholder with no novelty or equations; there is no upload endpoint. Reference deck: MathJax 3 + React Flow, plain-black equations in headed cards with a "Conexión" line and a lema.
- **L3** Decision (S6): KaTeX 0.16.22 vendored (synchronous, offline, testable in node) instead of MathJax; tutor as a harness skill/agent run headless with the user's own agent CLI (`claude -p` with `--tools Read`, `--json-schema`; `pi -p @image` fallback), so no API key lives in the dashboard; tutor routes reuse the terminal secret cookie and same-origin guard.
- **L4** (2026-10-20) Cost: a bare `claude -p` turn cost 0.73 USD with the user's settings (plugins/hooks), 0.006 USD with `--setting-sources local --strict-mcp-config --system-prompt`; `--bare` cannot be used (it skips the keychain login). `claude -p` read the parent's stdin into the prompt until `stdin=DEVNULL`. Live turn: 24–26 s, transcribed the page, found the planted missing modulus-squared, asked one Socratic question, rated 1 · reconoce with quoted evidence.
