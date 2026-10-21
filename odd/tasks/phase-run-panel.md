# Feature: follow a running phase from anywhere, keep its agent session, stop it

Objective: while a phase runs, the operator browses the dashboard freely and returns to the run from the dock or the CLI. The agent session survives navigation, closing the CLI and reloads, and the run can be stopped.
Branch: `feat/phase-run-panel` · Delivery: ask-on-risk · Runners: `.venv/bin/python -m pytest`, node harness tests.

## Specs

- **S1** "si quiere volver a ver el detalle del avance de dicha fase, de clic en la barra inferior izquierde de avance del proceso … al dar clic en la barra de avance del proceso, se debe mostrar los checkpoints e informacion base como la qye ya estabamos mostrando en la ejecucion de la fase": a click on a dock item opens a floating tracking panel on the current tab. It shows the same checkpoints and base information as the drawer tracker, and the user does not leave the tab.
- **S2** "si se le da al agente cli se debe ver la sesion qeu se tiene en dicha fase ejecutando": the CLI (FAB, or "Ver terminal" in the panel) shows the session the phase was sent to. When that session is gone, the panel says so.
- **S3** "verifica que no se caiga el cli o no tenga problemas al navegar por el tablero o cerrar el cli con una fase ejecutada, la fase debe seguir":
  - Moving between tabs and closing the CLI window never end the session.
  - A reload reattaches the live session instead of killing it while a phase run is live.
  - The output replayed on reattach or reconnect is drawn once, not duplicated.
- **S4** "agrega un boton en el panel de seguimiento de la fase … que sea detener proceso": a "Detener proceso" button interrupts the agent's turn (Esc for an agent, Ctrl-C for the shell). It keeps the session and marks the run as stopped by the operator.
- **S5** (assumption) The paste ends mid-sentence: "la infromacin de avance de la fase". It is read as asking that the run's progress information persist across navigation and reloads, which the localStorage-backed run store already does.

## Tasks

| ID | Specs | Route | Status | Commit |
|----|-------|-------|--------|--------|
| T1 | S2, S3 (server session lookup; CLI reattach, keep on unload, replay once, interrupt) | inline | done (RED 8 → GREEN) | see L3 |
| T2 | S1, S2, S4 (floating panel, stop, session note) | inline | done (RED 7 → GREEN) | see L3 |
| T3 | all (live check, docs, kit) | inline | done (live check L3) | see L3 |

## Log

- **L1** (2026-10-21, user request verbatim): "revisa el flujo, para que al ejecutar e iniciar o avanzar en una fase y se genere la barra de avance y el reloj del proceso, el usuario pueda navegar en el tablero ui, y si quiere volver a ver el detalle del avance de dicha fase, de clic en la barra inferior izquierde de avance del proceso, o en el cli del agente para la terminal con el proceso del agente. al dar clic en la barra de avance del proceso, se debe mostrar los checkpoints e informacion base como la qye ya estabamos mostrando en la ejecucion de la fase, si se le da al agente cli se debe ver la sesion qeu se tiene en dicha fase ejecutando. verifica que no se caiga el cli o no tenga problemas al navegar por el tablero o cerrar el cli con una fase ejecutada, la fase debe seguir. agrega un boton en el panel de seguimiento de la fase que se abre al dar clic en la barra de la fase que sea detener proceso. la infromacin de avance de la fase"
- **L2** Evidence:
  - The dock (`phase-run.js` renderDock) jumps to the Pipeline tab and opens the drawer, so the user loses the tab they were on.
  - `cli-console.js` deletes the session on `beforeunload`: a reload kills the agent while the run still shows "en ejecución".
  - The SSE stream (`server.py` `_terminal_stream`) replays from offset 0 on every connect, so an EventSource reconnect duplicates the screen.
  - Navigation is hash-based and closing the CLI only hides it, so both already keep the session.
- **L3** (2026-10-21) Live check on a scratch workspace (`smith ui` :8093), with a shell loop standing in for the agent:
  - Fase 2 was run, the CLI closed and the tab switched to #archify. A dock click opened the panel on #archify with the five checkpoints, "Detener proceso", "Ver terminal del agente" and "Abrir en Pipeline".
  - On reload, the same session id was reattached, the run was still live and the output appeared once (tick 1–3, not duplicated).
  - "Detener proceso" sent ^C (the loop ended), the session was kept, and the panel and dock show "⏹ detenida".
