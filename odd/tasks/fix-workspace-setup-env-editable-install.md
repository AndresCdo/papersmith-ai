# Fix: workspace setup_env.py falla en `pip install -e` (sin pyproject.toml)

## Problema
`papersmith init <dir>` corre `python3 scripts/setup_env.py install` dentro del
workspace nuevo. El `cmd_install()` hace `pip install -e PROJECT_ROOT` con
`check=True`. El workspace no es un proyecto Python (sin `pyproject.toml` ni
`setup.py`, solo `requirements.txt`), así que pip falla con
`does not appear to be a Python project` y aborta antes de instalar
`marker-pdf==2.0.0`. Resultado medido: env conda OK (`fastapi` importa,
`papersmith ui` anda), pero `OCR Engine Missing` y `/paper-ingestion` roto.

## Decisión aprobada por el usuario
Guardar el paso editable: solo correrlo cuando `PROJECT_ROOT` tenga
`pyproject.toml` o `setup.py`; si no, loguear el skip y seguir a `marker-pdf`.
Editar solo `scripts/setup_env.py` (fuente); regenerar el kit con
`python3 scripts/build-kit.py --quiet` (nunca editar `_kit` a mano).
Agregar test de regresión (Strict TDD). El workspace `~/papers/sparse-ae` fue
eliminado por el usuario: verificación por tests unitarios, no e2e en vivo.

## Tareas
1. [done] Guard + test de regresión (ejecutado inline por restricción no-kimi-k3)
2. [done] Kit regenerado + tests enfocados verdes
3. [in_progress] Reporte de evidencia al usuario
