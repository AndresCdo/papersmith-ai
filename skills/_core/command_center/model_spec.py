"""Conceptual and mathematical model specification.

Defines the formal domains, core equations, cost functions, optimization problems,
and proof-of-concept experimental plan for paper workspaces.

A workspace that wants its own specification writes it to
``.papersmith/model_spec.json``; otherwise this module answers a neutral
specification built only from ``papersmith.yaml``. No project's data ships with
the framework; the test suite carries one worked example under ``tests/fixtures/``.
"""

import json
from pathlib import Path
from typing import Any


def get_model_specification(root_path: Path | None = None) -> dict[str, Any]:
    """Return the structured specification of conceptual architecture,
    mathematical modeling, and proof-of-concept plan for a workspace."""
    if root_path is not None:
        root = Path(root_path).expanduser().resolve()
        spec_json = root / ".papersmith" / "model_spec.json"
        if spec_json.is_file():
            try:
                return json.loads(spec_json.read_text(encoding="utf-8"))
            except Exception:
                pass

        yaml_file = root / "papersmith.yaml"
        title = ""
        topic = ""
        authors_str = "Sin autor asignado"
        venue = "unspecified"
        if yaml_file.is_file():
            try:
                import yaml
                data = yaml.safe_load(yaml_file.read_text(encoding="utf-8")) or {}
                title = data.get("title", "")
                topic = data.get("topic", "")
                venue = data.get("venue_target", "unspecified")
                authors_list = data.get("authors", [])
                if isinstance(authors_list, list) and authors_list:
                    authors_str = ", ".join(a if isinstance(a, str) else a.get("name", "") for a in authors_list if isinstance(a, (str, dict)))
            except Exception:
                pass

        # Dynamic clean model specification for this workspace
        project_title = title or root.name
        return {
            "title": project_title,
            "target_journal": venue,
            "authors": authors_str,
            "trl": "Fase Inicial (Pendiente de deliberación)",
            "executive_summary": (
                f"Modelo conceptual y formal para el proyecto {project_title}. "
                "La arquitectura conceptual, el modelo matemático y el plan de prueba de concepto "
                "se formalizan durante la Fase 4 (Deliberación de Propuesta en proposals/) y la "
                "Fase 5 (Deliberación Experimental en experiments/)."
            ),
            "novelty": {
                "problem_statement": f"Planteamiento del problema y brecha técnica para {project_title} en proceso de deliberación.",
                "pillars": [
                    {
                        "id": "pillar-1",
                        "name": "Pilar 1: Innovación Metodológica / Teórica",
                        "badge": "CONCEPTUAL",
                        "color": "#38bdf8",
                        "summary": f"Contribución principal de {project_title}.",
                        "details": "Pendiente de formalización durante deliberación de propuesta (proposals/)."
                    },
                    {
                        "id": "pillar-2",
                        "name": "Pilar 2: Arquitectura del Sistema",
                        "badge": "ARQUITECTURA",
                        "color": "#10b981",
                        "summary": "Diseño y estructura técnica del sistema.",
                        "details": "Pendiente de andamiaje y verificación empírica."
                    },
                    {
                        "id": "pillar-3",
                        "name": "Pilar 3: Validación Empírica & Contrastes",
                        "badge": "METROLOGÍA",
                        "color": "#f59e0b",
                        "summary": "Protocolos de prueba y métricas de rendimiento.",
                        "details": "Pendiente de ejecución de experimentos (experiments/)."
                    }
                ]
            },
            "conceptual_map": {
                "layers": [
                    {"layer": "Capa 1: Insumos & Datos", "desc": "Datos crudos, referencias bibliográficas e instrumentación."},
                    {"layer": "Capa 2: Preprocesamiento & Feature Extraction", "desc": "Acondicionamiento y representaciones latentes."},
                    {"layer": "Capa 3: Núcleo Algorítmico", "desc": "Modelos teóricos, matemáticos o de aprendizaje automático."},
                    {"layer": "Capa 4: Inferencia & Métricas", "desc": "Evaluación cuantitativa y funciones de costo."},
                    {"layer": "Capa 5: Síntesis & Manuscrito", "desc": "Redacción técnica y compilación PDF."}
                ]
            },
            "mathematical_model": {
                "domains": [
                    {"name": "Espacio de Entrada", "symbol": "X", "definition": "Dominio de observaciones y datos de entrada."},
                    {"name": "Espacio de Salida", "symbol": "Y", "definition": "Dominio de predicción o transducción."}
                ],
                "equations": [],
                "optimization_problems": []
            },
            "poc_plan": {
                "experiments": []
            }
        }

    return get_model_specification(Path("Paper"))
