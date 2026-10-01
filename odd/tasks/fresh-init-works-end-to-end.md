# Batch: init deja todo andando (post tgce-ss eliminado)

## Contexto
El usuario eliminó `~/papers/sparse-ae` y luego `~/papers/tgce-ss`. Pide que el
main quede bien para que un `init` fresco funcione de punta a punta. Tres gaps
confirmados con evidencia: (1) template sin `paper_writing.roles` (RESOLVER_ROLE_EMPTY
en workspaces nuevos); (2) `_arxiv_url` no saca el prefijo `arXiv:` (feed vacío,
probado en vivo 706 vs 2814 bytes); (3) 19 agentes solo en `.claude/agents`,
Pi no los ve (descubre `<cwd>/.pi/agents/*.md`, formato verificado contra
`lib/agents-config.ts` de gentle-pi). Restricción vigente: no lanzar subagentes
con kimi-k3 (sin parámetro de modelo en el esquema) → ejecución inline.
Git del workspace: no tocar (decisión del usuario).

## Tareas
1. [done] Roles en `papersmith.yaml.tpl` + test de init
2. [done] Fix prefijo arXiv + mapeo de error + tests
3. [done] Proyector pi-agents + cableado init/upgrade + tests
4. [done] Verificación con init offline en /tmp + reporte

## Evidencia
- `test_paper_resolve.py` (nuevo, 3 tests) + `test_paper_writing.py`: 684 passed
- `test_papersmith_generators.py`: 28 passed (3 nuevos)
- init/generators/kit/upgrade/commands/skills e2e: 118 passed, 2 failed
  preexistentes en main limpio (falta `jiti`, sin red)
- Init offline en /tmp: roles presentes, 19 `.pi/agents/`, drift none
