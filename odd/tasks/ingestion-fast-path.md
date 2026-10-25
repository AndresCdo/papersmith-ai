# ingestion-fast-path

Objective: make paper ingestion fast and license-unrestricted: route each PDF page to a permissive fast path (pypdfium2) or a permissive heavy engine (Docling) only when needed, cache per page by content hash, and write a JSON sidecar with a fragment tool.
Branch: feat/ingestion-fast-path · Delivery: ask-on-risk · Runners: pytest (tests/test_extract_pdf.py, tests/test_pdf_pipeline.py), real-PDF measurement on arXiv 1706.03762 and 1312.6114.

## Specs

- S1 (alternative 1) Route per page, only when needed: probe every page without models (text layer, math-font glyphs, table cues, image-only pages); digital prose pages take the fast path, scanned / equation-dense / table pages go to the heavy engine through its page range.
- S2 (alternative 2) Cache by content hash: per page, keyed by the PDF's sha256, the route, the engine version and its options; verifiable (each entry carries its own hash) and reused on re-ingest.
- S3 (alternative 3) A JSON sidecar beside the `.md` (pages with Markdown offsets, routes and engines, headings, equations, references kept per page, figures, timings) and a tool that returns one fragment (page, heading, equation, search) without the whole document, exposed as a script and as the MCP tool `papersmith.ingest_fragment`.
- S4 "asegurate de usar alternativas que no tengan limites por ingresos, que puedan ser rapidas, eficientes y sin restricciones": default engines must carry no revenue/user thresholds and no copyleft: pypdfium2 (Apache-2.0/BSD-3; PDFium BSD), Docling (MIT) with docling-layout-heron (Apache-2.0), CodeFormulaV2 (CDLA-Permissive-2.0), RapidOCR (Apache-2.0). Marker (weights: modified OpenRAIL-M, free only under USD 5M funding/revenue) and MinerU (license threshold: USD 20M monthly revenue or 100M MAU) are not defaults; Marker stays an explicit opt-in engine with a license notice. PyMuPDF (AGPL, unused) leaves the installer.

Assumptions: existing workspaces that set `engine: marker` keep Marker (their stored config is not rewritten); new defaults are `engine: auto`. Benchmarks beyond the measured runs and other engines are out of scope (user approved items 1-3).

## Tasks

- T1 S1,S4 inline — pdf_pipeline.py: page probe + routing + fast-path Markdown (pypdfium2), unit tests on generated PDFs. Status: done (tests written after a spike on real PDFs; 6 mutations of routing/cache rules each killed by a test)
- T2 S1,S4 inline — Docling adapter (page ranges, formulas as LaTeX, OCR only for scanned pages) + engine selection auto|pdfium|docling|marker in extract_pdf.py, page markers, config validation. Status: done
- T3 S2 inline — per-page content-hash cache with verification. Status: done
- T4 S3 inline — JSON sidecar + pdf_fragment.py + MCP tool papersmith.ingest_fragment. Status: done (surface 'skill'; 4 MCP integration tests)
- T5 S4 inline — installer (setup_env.py, requirements, setup.sh), papersmith.yaml + template, CI note, SKILL.md, README, CHANGELOG, license table. Risk item 5. Status: done (harness projection resynced)
- T6 S1-S4 delegated (verification trigger: installer/dependency change) — independent verifier + real-PDF timings. Status: done (S1-S4 PASS, no blockers; advisories A1, A2, A4, A5 fixed in one correction batch with RED-proven tests; A3 model LaTeX spacing and A6 thin Marker sidecar left as advisories)

## Log

- L1 (2026-10-21) "explora las fases que requieren la ingesta de pdfs. a partir del siguiente propmt explora alternativas para optimizar dicha ingesta, cuando es necesario, en el fujo del proyecto" (plus the pasted master prompt).
- L2 (2026-10-21) "si, y asegurate de usar alternativas que no tengan limites por ingresos, que puedan ser rapidas, eficientes y sin restricciones" — approves items 1-3 of the exploration.
- L3 Licenses verified from primary sources: pypdfium2 README (Apache-2.0/BSD-3), Docling README (MIT; models per card), HF cards docling-layout-heron (apache-2.0) and CodeFormulaV2 (cdla-permissive-2.0), MinerU LICENSE.md (thresholds 20M USD/month or 100M MAU), Marker README (weights free under 5M funding/revenue). Installed metadata: docling/docling-core/docling-ibm-models/docling-parse MIT, rapidocr Apache-2.0.
- L4 Probe spike: pypdfium2 per-char font scan of 3 pages of 1312.6114 took 0.23 s; math glyphs show up as CMMI*/CMSY*/CMEX* fonts, distinct from body CMR/Nimbus. `DocumentConverter.convert(..., page_range=(a, b))` exists (1-based, inclusive).
- L5 Docling formula model: CodeFormulaV2 does not run on MPS and took 253 s for one page on CPU; Granite-Docling-258M (Apache-2.0) on MLX took 7 s. Formula backend now follows the hardware; CPU-only keeps math pages on the fast path unless formulas_on_cpu.
- L6 Marker baseline measured (fast mode, warm): 6.8 s Attention, 28.2 s VAE. First auto run was slower (46 s / 34 s); profiling showed TableFormer at 90 % of Docling time. Fixes: display-equation line detection instead of glyph counts, citation brackets excluded from table rows, TableFormer FAST mode and only on runs with table cues -> 21.5 s / 28.6 s. Display equations as LaTeX: 6 / 30 (Marker 1 / 23). Cached re-ingest 0.2 s.
- L7 RapidOCR needs a backend: torch (already installed) instead of adding onnxruntime; language 'en' (default is Chinese). Scanned 2-page PDF read correctly.
- L8 Assumption kept: PyMuPDF removed from installer/requirements (no import anywhere); Marker kept as opt-in engine with a license notice; existing workspaces' engine: marker is honored, not rewritten.
- L9 Verifier (independent): S1-S4 PASS, 169 tests, CLI end to end in a scratch workspace, cache tamper detection, licenses from installed metadata, strip_references and --list identical to baseline 5a085d51. Advisory A1 (a lone recomputed Docling page differs from its run) reproduced and fixed: heavy keys carry the run and a miss reconverts the run; real VAE re-check after deleting page 5's entry -> pages 3-5 reconverted, .md identical.
- L10 Pre-existing failures (also on main, worktree check): test_command_center_paper_preview case test (macOS case-insensitive FS), test_version_sources release hygiene (13 shipped files changed since v0.18.0), kaggle vocabulary subtests; test_command_center_smoke needs fastapi in .venv.
- L11 RDD: assess high (setup_env process boundary, CI shell). Consent granted; 4-lens review ran (all captures exit 0), final capture opened correction_required. Its status_continuation dropped the START's untracked-scope selectors and demanded `intended_untracked_selection` (uv.lock, unrelated) in an undocumented exact JSON; 16 bounded, retry-safe submissions all rejected (invalid_request, mutation not_started). Classified as a Gentle AI 4.1.1 provider defect; with the user's consent ("Reportar y continuar") an occurrence comment was added to canonical issue #5129 (no published fix; v4.2.0 notes silent). The captured decline invocation ran once: action declined, consent declined_this_candidate, target matched. The review's correction findings were never surfaced to the consumer, so they are unknown, not resolved. Delivery follows ordinary repository policy.
