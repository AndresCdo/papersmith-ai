"""What each pipeline phase card lets the operator do from the dashboard.

A phase runs one of three ways, and the drawer offers exactly these:

* ``prompt`` — the stage is a harness slash command (``/<skill> $ARGUMENTS``,
  projected to ``.claude/commands``, ``.opencode/commands`` and ``.pi/prompts``).
  The drawer shows a text box with the skill's input rules as a guide, and
  "Ejecutar" types ``/<skill> <text>`` into the support terminal's agent.
* ``command`` — a real ``papersmith`` subcommand, typed into a shell session.
* ``redirect`` — the work happens in another dashboard panel (the concept map,
  the math tutor, the PoC board, the PDF preview…), so the drawer opens it.

Every slash command named here exists as a projected command and every shell
command is a ``papersmith`` subcommand the CLI accepts; tests hold both.
"""

from __future__ import annotations

import copy
from typing import Any

# The phase order of the "Fases del Pipeline" panel; ``Fase N`` is index N-1.
STAGES: tuple[str, ...] = (
    "harness", "plausibility", "ingestion", "proposal", "poc_experiments",
    "scaffolding", "declarations", "writing", "figures", "paper", "audit",
)


def _prompt(slash: str, label: str, guide: list[str], placeholder: str, *,
            min_sentences: int = 0, optional: bool = False, prefix: str = "") -> dict[str, Any]:
    return {"kind": "prompt", "slash": slash, "label": label, "guide": guide,
            "placeholder": placeholder, "min_sentences": min_sentences,
            "optional": optional, "prefix": prefix}


def _command(command: str, label: str, desc: str) -> dict[str, Any]:
    return {"kind": "command", "command": command, "label": label, "desc": desc}


def _redirect(label: str, tab: str, desc: str, section: str = "") -> dict[str, Any]:
    return {"kind": "redirect", "label": label, "tab": tab, "section": section, "desc": desc}


_WRITING_GUIDE = [
    "Nombra un bloque o una acción: abrir el árbol paper/, ver qué fase de escritura está desbloqueada, o escribir un bloque.",
    "Un bloque se escribe solo: el agente nunca toca otro byte de paper/main.tex.",
    "Cada afirmación necesita una fuente que la sostenga (resolve); sin fuente, no se escribe.",
    "Escribe en el idioma del paper; el registro y el estilo vienen de las declaraciones.",
]

ACTIONS: dict[str, dict[str, Any]] = {
    "harness": {
        "skills": ["upgrade-project"],
        "agent": "papersmith CLI",
        "actions": [
            _command("papersmith status .", "Ver estado del workspace",
                     "Resumen del workspace: kit, harnesses, etapas y artefactos."),
            _command("papersmith audit . --check-drift", "Verificar proyecciones",
                     "Comprueba que .claude, .opencode, .pi y .agents coinciden con el kit."),
            _prompt("/upgrade-project", "Actualizar el workspace (agente)", [
                "Úsalo cuando el workspace corre una versión anterior de papersmith.",
                "El agente trae skills, agentes, comandos y formas de artefacto a la versión instalada.",
                "Opcional: indica qué quieres conservar o revisar antes de actualizar.",
            ], "Ej.: actualiza el workspace y dime qué cambió en los comandos.", optional=True),
        ],
    },
    "plausibility": {
        "skills": ["plausibility"],
        "agent": "sota-scout → sota-grapher → novelty-screener",
        "actions": [
            _prompt("/plausibility", "Explorar la plausibilidad de la idea", [
                "Escribe la idea en al menos dos oraciones: el problema y lo que propones (si no, el agente se niega a buscar).",
                "El agente reúne ~25 referencias SOTA por sus abstracts, en 3 a 5 familias, y dibuja la constelación (atlas.html).",
                "Luego divide la hipótesis en afirmaciones y califica cada una (novel / known / tension / contradicted) con citas literales.",
                "Nada se ingiere ni se archiva: el informe espera tu aceptación antes de pasar el top 5 a ingestión.",
                "Puedes ajustar la idea y pedir un nuevo screening; cada pasada es un informe nuevo.",
            ], "Ej.: Los modelos actuales pierden precisión fuera de su dominio de entrenamiento. Propongo …",
                min_sentences=2),
            _redirect("Ver la constelación SOTA", "atlas", "Atlas 3D del pool de candidatos."),
        ],
    },
    "ingestion": {
        "skills": ["paper-ingestion"],
        "agent": "paper-ingestion",
        "actions": [
            _prompt("/paper-ingestion", "Ingerir referencias", [
                "Indica la ruta o URL de los PDF a ingerir (normalmente el top 5 aceptado en plausibilidad).",
                "Cada PDF se archiva en su carpeta de tema y se convierte a Markdown: ecuaciones en LaTeX, tablas en Markdown, figuras como archivos.",
                "Local y sin llaves (Marker); nada se publica.",
            ], "Ej.: ingiere guidance/reference-papers/inbox/*.pdf"),
            _command("papersmith ingest <ruta-o-url> .", "Ingerir desde el CLI",
                     "Reemplaza <ruta-o-url> por el PDF o la URL."),
            _redirect("Ver artefactos ingeridos", "artifacts", "Markdown y figuras de las referencias."),
        ],
    },
    "proposal": {
        "skills": ["proposal-deliberation", "math-tutor"],
        "agent": "proposal-deliberation & math-tutor",
        "actions": [
            _prompt("/proposal-deliberation", "Deliberar la propuesta", [
                "Pide la primera versión, un cambio a la propuesta vigente o una operación de revisión (rNN).",
                "El agente es tutor: discute antes de decidir y no aplica un cambio sin tu aprobación.",
                "La matemática se escribe en bloques $$ … \\tag{N} $$; la novedad se ubica dentro del cielo SOTA.",
                "Las guías de dominio en guidance/paper-guide/ se cargan solas.",
            ], "Ej.: discutamos si la hipótesis H2 sigue en pie con la referencia de Smith 2024."),
            _redirect("Discutir el mapa conceptual", "modelo",
                      "Pilares, hipótesis y capas del concepto.", "mapa"),
            _redirect("Matemática y tutor socrático", "modelo",
                      "Ecuaciones en LaTeX, tarjeta de novedad y tutor con imágenes a mano.", "matematico"),
        ],
    },
    "poc_experiments": {
        "skills": ["experimental-deliberation", "proposal-implementation",
                   "experimental-implementation", "kaggle-accounts", "remote-execution"],
        "agent": "experimental-deliberation & proposal/experimental-implementation",
        "actions": [
            _prompt("/experimental-deliberation", "Deliberar el diseño experimental", [
                "Pregunta que gobierna cada turno: ¿qué experimento pondría a prueba esta afirmación de la propuesta?",
                "Cada experimento declara la afirmación que prueba, su métrica y su baseline SOTA.",
                "Pide la primera versión, un cambio o una operación de revisión; nada se aplica sin tu aprobación.",
            ], "Ej.: diseña el experimento que prueba la afirmación C1 contra el baseline más fuerte del SOTA."),
            _prompt("/proposal-implementation", "Implementar la prueba de concepto", [
                "Convierte la última propuesta en Python contra un repositorio objetivo, o verifica una implementación existente.",
                "Indica el repositorio objetivo y si es primera pasada o una pasada posterior.",
            ], "Ej.: implementa la PoC de la propuesta r03 en ../mi-poc", optional=True),
            _prompt("/experimental-implementation", "Implementar y medir los experimentos", [
                "Convierte el protocolo experimental vigente en Python y corre sus mediciones declaradas.",
                "Indica el repositorio objetivo; la verificación compara contra el protocolo y la propuesta.",
            ], "Ej.: implementa E1 y E2 y reporta las métricas.", optional=True),
            _prompt("/remote-execution", "Ejecución remota (Kaggle / workers)", [
                "Envía entrypoints a un worker remoto y lee lo que regresó; el ledger es de solo anexar.",
                "Si las cuentas no autentican, usa primero /kaggle-accounts.",
            ], "Ej.: envía experiments/e1.py al mejor worker disponible.", optional=True),
            _redirect("Ver el tablero PoC", "modelo", "Experimentos y veredictos de la prueba de concepto.", "poc"),
        ],
    },
    "scaffolding": {
        "skills": ["paper-writing"],
        "agent": "paper-writing",
        "actions": [
            _prompt("/paper-writing", "Abrir el árbol del paper", _WRITING_GUIDE,
                    "Ej.: abre el esqueleto de secciones y bloques del paper.", prefix="skeleton "),
            _redirect("Ver secciones del paper", "sections", "Contratos de sección y bloques canónicos."),
        ],
    },
    "declarations": {
        "skills": ["paper-writing"],
        "agent": "paper-writing (mark)",
        "actions": [
            _prompt("/paper-writing", "Registrar una declaración", [
                "Una declaración fija una decisión del paper: autoría CRediT, financiación, datos y código, ética, idioma o estilo.",
                "Escribe la declaración y su valor; queda registrada con su procedencia (mark).",
            ], "Ej.: idioma del manuscrito: inglés; disponibilidad de código: GitHub público.", prefix="mark "),
            _redirect("Ver secciones del paper", "sections", "Declaraciones y bloques del manuscrito."),
        ],
    },
    "writing": {
        "skills": ["paper-writing"],
        "agent": "paper-writing (redactor)",
        "actions": [
            _prompt("/paper-writing", "Escribir un bloque", _WRITING_GUIDE,
                    "Ej.: escribe el bloque intro.motivation"),
            _redirect("Ver secciones del paper", "sections", "Estado de cada bloque."),
            _redirect("Ver el PDF", "preview", "Previsualización de paper/main.pdf."),
        ],
    },
    "figures": {
        "skills": ["figure-review"],
        "agent": "figure-review",
        "actions": [
            _prompt("/figure-review", "Revisar una figura", [
                "Indica el id de la figura ya compilada en paper/Figures/<id>.pdf.",
                "La revisión juzga si la imagen se lee por sí misma, no el texto que la describe.",
            ], "Ej.: revisa la figura fig-architecture"),
            _redirect("Ver el PDF", "preview", "Figuras en el manuscrito compilado."),
        ],
    },
    "paper": {
        "skills": ["paper-writing"],
        "agent": "pdflatex",
        "actions": [
            _redirect("Ver el PDF", "preview", "Visor PDF con recarga en vivo."),
        ],
    },
    "audit": {
        "skills": ["skill-audit"],
        "agent": "skill-audit & papersmith audit",
        "actions": [
            _command("papersmith audit . --verbose", "Auditar el workspace",
                     "Estructura y consistencia del workspace."),
            _prompt("/skill-audit", "Auditar un skill o un CLI", [
                "Nombra el sujeto: un skill, un CLI o cualquier conjunto cerrado (operaciones, subcomandos, códigos de error).",
                "La auditoría busca la brecha entre lo que el código acepta y lo que su documentación afirma.",
            ], "Ej.: audita skills/paper-writing"),
            _redirect("Ver compuertas", "gates", "Estado de las compuertas del framework."),
        ],
    },
}


def stage_for(phase_id: str) -> str | None:
    """The stage a ``/api/phase/run`` id names: a stage id, or ``Fase N``."""
    text = str(phase_id or "").strip()
    if text in STAGES:
        return text
    parts = text.split()
    if len(parts) == 2 and parts[0].lower() == "fase" and parts[1].isdigit():
        index = int(parts[1]) - 1
        if 0 <= index < len(STAGES):
            return STAGES[index]
    return None


def primary_command(stage: str) -> str:
    """The text the drawer shows as the phase's command."""
    for action in ACTIONS.get(stage, {}).get("actions", []):
        if action["kind"] == "prompt":
            return f"{action['slash']} <texto>" if not action["optional"] else action["slash"]
        if action["kind"] == "command":
            return action["command"]
    return "Compilar desde el tablero (pdflatex + bibtex)" if stage == "paper" else ""


def attach(fases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Add each phase's actions, real skills and command to the status view."""
    for phase in fases:
        entry = ACTIONS.get(phase.get("stage_id", ""))
        if not entry:
            continue
        phase["actions"] = copy.deepcopy(entry["actions"])
        phase["skills"] = list(entry["skills"])
        phase["agent"] = entry["agent"]
        phase["cli_command"] = primary_command(phase["stage_id"])
    return fases


__all__ = ["ACTIONS", "STAGES", "attach", "primary_command", "stage_for"]
