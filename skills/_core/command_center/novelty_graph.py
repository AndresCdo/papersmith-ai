"""3D semantic novelty graph of a paper workspace.

The graph a workspace provides in ``.papersmith/novelty_graph.json`` (nodes,
links, groups; the shape ``build_novelty_graph`` returns) is drawn as-is.
Without it, a neutral initial graph named after the workspace is drawn, whose
nodes the deliberation phases populate. No project's graph ships with the
framework; the test suite carries one worked example under ``tests/fixtures/``.
"""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

def build_novelty_graph(root_path: Path | None = None) -> dict[str, Any]:
    """The workspace's own ``.papersmith/novelty_graph.json`` when it holds a
    graph, else a neutral initial graph named after the workspace."""
    if root_path is not None:
        own = Path(root_path) / ".papersmith" / "novelty_graph.json"
        try:
            data = json.loads(own.read_text(encoding="utf-8"))
            if isinstance(data, dict) and isinstance(data.get("nodes"), list):
                return data
        except (OSError, ValueError):
            pass

    project_name = root_path.name if root_path else "Paper"
    return {
        "title": f"Grafo 3D de Novedad e Ideas del Manuscrito — {project_name}",
        "target_journal": "Objetivo Editorial",
        "authors": "Equipo de Investigación",
        "project": project_name,
        "summary": f"Estructura conceptual en fase inicial para {project_name}. Los nodos semánticos se pueblan durante las fases 2 (SOTA), 4 (Deliberación de Propuesta) y 5 (PoC Experimental).",
        "nodes": [
            {
                "id": "core-project",
                "label": f"{project_name}: Propuesta en Deliberación",
                "group": "core",
                "color": "#38bdf8",
                "size": 9.0,
                "category": "Contribución Global",
                "badge": "ARQUITECTURA PRINCIPAL",
                "desc": f"Marco de trabajo e investigación para {project_name} en fase inicial de formulación.",
                "rhetorical_question": f"¿Cuál es la hipótesis central y contribución esperada de {project_name}?",
                "paragraph_text": f"El proyecto {project_name} se encuentra en etapa inicial de deliberación de propuesta científica y acoplamiento con el estado del arte.",
                "metrics": "Fase 1 completada (Harness). Fases de deliberación y experimentación pendientes.",
                "novelty_claim": "Innovación metodológica y teórica en formalización.",
                "thesis_ref": "Insumos en guidance/",
                "pdf_page": 1,
                "section_ref": "Sección 1 (Introducción)",
                "paper_blocks": ["title-and-keywords.title", "abstract.slot-1", "introduction.block-1"]
            },
            {
                "id": "hub-problem",
                "label": "Problema & Brecha Técnica",
                "group": "problem",
                "color": "#ef4444",
                "size": 7.0,
                "category": "Desafíos",
                "badge": "BRECHA CIENTÍFICA",
                "desc": "Limitaciones y cuellos de botella en las aproximaciones actuales.",
                "rhetorical_question": "¿Qué problema fundamental no resuelto aborda esta investigación?",
                "paragraph_text": "Pendiente de formalización durante Fase 4.",
                "metrics": "Pendiente",
                "novelty_claim": "Definición rigurosa de la brecha científica.",
                "thesis_ref": "proposals/",
                "pdf_page": 1,
                "section_ref": "Sección 1 (Introducción)",
                "paper_blocks": ["abstract.slot-2", "introduction.block-2"]
            },
            {
                "id": "hub-sota",
                "label": "Constelación SOTA & Baselines",
                "group": "sota",
                "color": "#10b981",
                "size": 7.0,
                "category": "Estado del Arte",
                "badge": "LITERATURA Q1",
                "desc": "Mapeo de sistemas comparativos y papers de referencia.",
                "rhetorical_question": "¿Cuáles son los baselines de referencia frente a los cuales se contrastará la propuesta?",
                "paragraph_text": "Atlas 3D en construcción en sota-pool/.",
                "metrics": "Pendiente",
                "novelty_claim": "Taxonomía comparativa con literatura especializada.",
                "thesis_ref": "sota-pool/atlas.json",
                "pdf_page": 3,
                "section_ref": "Sección 2 (Related Work)",
                "paper_blocks": ["related-work.rw-preamble", "related-work.rw-panorama"]
            },
            {
                "id": "hub-novelty",
                "label": "Metodología & Arquitectura",
                "group": "novelty",
                "color": "#f59e0b",
                "size": 7.0,
                "category": "Innovación",
                "badge": "PILAR METODOLÓGICO",
                "desc": "Componentes, formulación matemática y diseño del sistema.",
                "rhetorical_question": "¿Cuál es la metodología o arquitectura propuesta para resolver la brecha?",
                "paragraph_text": "Pendiente de especificación formal.",
                "metrics": "Pendiente",
                "novelty_claim": "Innovación algorítmica / arquitectónica.",
                "thesis_ref": "sections/01-materials-and-methods.md",
                "pdf_page": 4,
                "section_ref": "Sección 3 (Materials and Methods)",
                "paper_blocks": ["materials-and-methods.mm-preamble", "materials-and-methods.mm-proposal"]
            },
            {
                "id": "hub-eval",
                "label": "Validación Empírica & Experimentos",
                "group": "eval",
                "color": "#a855f7",
                "size": 7.0,
                "category": "Metrología",
                "badge": "PROTOCOLO POC",
                "desc": "Diseño experimental, métricas de éxito y contrastes empíricos.",
                "rhetorical_question": "¿Cómo se validarán cuantitativamente las hipótesis del trabajo?",
                "paragraph_text": "Plan experimental en experiments/.",
                "metrics": "Pendiente",
                "novelty_claim": "Criterios de éxito reproducibles.",
                "thesis_ref": "experiments/",
                "pdf_page": 5,
                "section_ref": "Sección 4 (Experimental Setup)",
                "paper_blocks": ["experimental-setup.es-preamble", "results-and-discussion.rd-general-task"]
            }
        ],
        "links": [
            {"source": "core-project", "target": "hub-problem", "label": "aborda", "value": 3.0},
            {"source": "core-project", "target": "hub-sota", "label": "supera", "value": 3.0},
            {"source": "core-project", "target": "hub-novelty", "label": "implementa", "value": 4.0},
            {"source": "core-project", "target": "hub-eval", "label": "valida con", "value": 3.5}
        ]
    }


def build_novelty_viewer_html(root_path: Path | None = None) -> str:
    """Generate the full responsive 3D WebGL viewer for the novelty graph,
    matching the exact style, typography, libraries, and constellation aesthetics of SOTA Atlas."""
    data = build_novelty_graph(root_path)
    graph_json = json.dumps(data, ensure_ascii=False)
    graph_title = html.escape(str(data.get("title", "Grafo 3D de Novedad e Ideas del Manuscrito")))
    graph_subtitle = html.escape(f"{data.get('target_journal', '')} · {data.get('project', '')}")
    core_label = json.dumps(str(data.get("project") or "Proyecto"), ensure_ascii=False)
    
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>{graph_title}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <script src="https://unpkg.com/3d-force-graph@1.73.3/dist/3d-force-graph.min.js"></script>
  <style>
    html, body {{
      height: 100%;
      margin: 0;
      padding: 10px 14px;
      box-sizing: border-box;
      background: #0a0a10;
      color: #e4e4ed;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }}
    h1 {{
      font-size: 16px;
      font-weight: 600;
      margin: 0 0 4px;
      letter-spacing: .02em;
      color: #f1f5f9;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    h1 small {{
      font-size: 11px;
      font-weight: 400;
      color: #64748b;
      letter-spacing: 0;
    }}
    #panel {{
      color: #9aa3bd;
      font-size: 12px;
      margin: 0 0 6px;
      line-height: 1.35;
    }}
    #famlegend, #rellegend, #toolbar {{
      margin: 0 0 5px;
      font-size: 12px;
      color: #9aa3bd;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
    }}
    #famlegend em, #rellegend em {{
      font-style: normal;
      font-weight: 600;
      margin-right: 6px;
      color: #cbd5e1;
    }}
    .famchip {{
      margin: 2px 4px 2px 0;
      padding: 2.5px 10px;
      cursor: pointer;
      border-radius: 12px;
      border: 1px solid #334155;
      background: #14172a;
      color: #e4e4ed;
      font-size: 11.5px;
      display: inline-flex;
      align-items: center;
      gap: 5px;
      transition: all 0.15s ease;
      user-select: none;
    }}
    .famchip:hover {{
      background: #1e243d;
      border-color: #475569;
    }}
    .famchip.on {{
      font-weight: 700;
      box-shadow: 0 0 10px currentColor;
    }}
    .famchip-dot {{
      width: 7px;
      height: 7px;
      border-radius: 50%;
      display: inline-block;
    }}
    .dot {{
      display: inline-block;
      width: 14px;
      height: 0;
      border-top: 2px solid;
      margin: 0 3px 2px 8px;
      vertical-align: middle;
    }}
    #toolbar {{
      gap: 6px;
    }}
    #toolbar button {{
      font-size: 12px;
      padding: 3.5px 11px;
      cursor: pointer;
      background: #14172a;
      color: #e4e4ed;
      border: 1px solid #2a3350;
      border-radius: 6px;
      transition: background 0.15s, border-color 0.15s;
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }}
    #toolbar button:hover {{
      background: #1e243d;
      border-color: #38bdf8;
    }}
    #toolbar button.active {{
      background: #0284c7;
      border-color: #38bdf8;
      color: #fff;
    }}
    #nodeSearchInput {{
      background: #14172a;
      border: 1px solid #2a3350;
      border-radius: 6px;
      padding: 3px 10px;
      font-size: 12px;
      color: #e4e4ed;
      outline: none;
      margin-left: 6px;
      width: 220px;
    }}
    #nodeSearchInput:focus {{
      border-color: #38bdf8;
      box-shadow: 0 0 8px rgba(56, 189, 248, 0.3);
    }}
    .sky {{
      flex: 1 1 auto;
      min-height: 420px;
      width: 100%;
      background: #0a0a10;
      border: 1px solid #1e2236;
      border-radius: 10px;
      overflow: hidden;
      position: relative;
      cursor: grab;
    }}
    .sky:active {{
      cursor: grabbing;
    }}
    #3d-graph {{
      width: 100%;
      height: 100%;
    }}

    /* Side Inspector Card (Modal Style matching SOTA Atlas) */
    .inspector-card {{
      position: absolute;
      top: 12px;
      right: 12px;
      width: 440px;
      max-width: calc(100vw - 28px);
      max-height: calc(100% - 24px);
      background: #11131f;
      border: 1px solid #2a3350;
      border-radius: 10px;
      padding: 16px 18px;
      overflow-y: auto;
      z-index: 20;
      box-shadow: 0 0 40px rgba(14, 165, 233, 0.2);
      display: none;
      scrollbar-width: thin;
    }}
    .inspector-card__header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
      padding-bottom: 6px;
      border-bottom: 1px solid #1e243d;
    }}
    .inspector-badge {{
      display: inline-block;
      font-size: 11px;
      font-weight: 700;
      padding: 2px 8px;
      border-radius: 4px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .inspector-close {{
      background: #1a1d2e;
      border: 1px solid #2a3350;
      color: #e4e4ed;
      font-size: 13px;
      padding: 1px 8px;
      border-radius: 4px;
      cursor: pointer;
    }}
    .inspector-close:hover {{
      background: #2a3350;
    }}
    .inspector-title {{
      font-size: 15px;
      font-weight: 700;
      color: #fff;
      margin-bottom: 6px;
      line-height: 1.3;
    }}
    .inspector-desc {{
      font-size: 12px;
      color: #94a3b8;
      line-height: 1.5;
      margin-bottom: 12px;
    }}
    .quote {{
      font-style: italic;
      color: #b9c4de;
      border-left: 3px solid #10b981;
      margin: 10px 0;
      padding: 8px 12px;
      background: rgba(16, 185, 129, 0.05);
      border-radius: 0 6px 6px 0;
      font-family: Georgia, serif;
      line-height: 1.55;
      font-size: 12.5px;
    }}
    .inspector-meta-block {{
      margin-bottom: 10px;
      font-size: 12px;
      line-height: 1.45;
    }}
    .inspector-meta-block strong {{
      color: #cbd5e1;
      display: block;
      margin-bottom: 3px;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}
    .inspector-meta-block em {{
      color: #38bdf8;
      font-style: normal;
    }}
    .inspector-meta-block span {{
      color: #94a3b8;
    }}
    .inspector-blocks {{
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
      margin-top: 4px;
    }}
    .block-pill {{
      background: rgba(56, 189, 248, 0.12);
      border: 1px solid rgba(56, 189, 248, 0.25);
      color: #38bdf8;
      padding: 1px 6px;
      border-radius: 3px;
      font-size: 10.5px;
      font-family: monospace;
    }}
    .btn-action-jump {{
      width: 100%;
      background: #0284c7;
      color: #fff;
      border: 1px solid #38bdf8;
      padding: 8px 12px;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      margin-top: 10px;
      transition: background 0.15s, transform 0.15s;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
    }}
    .btn-action-jump:hover {{
      background: #0369a1;
      transform: translateY(-1px);
    }}
  </style>
</head>
<body>

  <!-- Top Title and Instructions (Atlas Style) -->
  <h1>
    <span>🕸️ {graph_title}</span>
    <small>{graph_subtitle}</small>
  </h1>
  <div id="panel">Arrastra con el ratón para rotar (órbita suave), rueda para zoom 3D sensible, clic derecho para desplazar. Clic en cualquier nodo para inspeccionar evidencia y párrafos. Usa los chips de colores para filtrar por las 8 dimensiones clave.</div>

  <!-- Legend & Color Grouping Chips (Atlas Style) -->
  <div id="famlegend"><em>8 Dimensiones Clave:</em> <span id="famchips"></span></div>
  <div id="rellegend"><em>Enlaces:</em> <span class="dot" style="border-color:#38bdf8"></span>arquitectura global <span class="dot" style="border-color:#10b981"></span>novedad vendida <span class="dot" style="border-color:#f43f5e"></span>resuelve brecha <span class="dot" style="border-color:#a855f7"></span>evidencia experimental <span class="dot" style="border-color:#eab308"></span>métricas comparativas</div>

  <!-- Toolbar Controls (Atlas Style) -->
  <div id="toolbar">
    <button id="zoomin" title="Acercar cámara">🔍 Zoom +</button>
    <button id="zoomout" title="Alejar cámara">🔍 Zoom −</button>
    <button id="zoomreset" title="Restablecer vista centrada">↺ Reset</button>
    <button id="btnAutoRotate" class="active" title="Pausar o reanudar giro suave de la cámara">⏸️ Pausar giro</button>
    <button id="btnWheelMode" title="Alternar función de la rueda del ratón">🖱️ Rueda: Zoom 3D</button>
    <input type="text" id="nodeSearchInput" placeholder="🔍 Buscar nodo, métrica o párrafo..." oninput="searchNodes(this.value)">
  </div>

  <!-- Sky Canvas Container -->
  <div id="sky" class="sky">
    <div id="3d-graph"></div>

    <!-- Side Inspector Drawer / Modal -->
    <aside class="inspector-card" id="inspectorCard">
      <div class="inspector-card__header">
        <span class="inspector-badge" id="inspBadge">Categoría</span>
        <button class="inspector-close" onclick="closeInspector()">✕ cerrar</button>
      </div>
      <div class="inspector-title" id="inspTitle">Nombre del Nodo</div>
      <p class="inspector-desc" id="inspDesc">Descripción detallada del nodo y su rol en la investigación.</p>
      
      <!-- Extracto del Párrafo del Manuscrito -->
      <div id="inspParagraphBox" style="display: none; margin-bottom: 10px;">
        <strong style="font-size: 11px; text-transform: uppercase; color: #cbd5e1; letter-spacing: 0.04em;">📜 Extracto del Párrafo del Manuscrito (LaTeX)</strong>
        <div class="quote" id="inspParagraphText">—</div>
      </div>

      <!-- Pregunta Retórica que Responde -->
      <div class="inspector-meta-block" id="inspQuestionBox">
        <strong>❓ Pregunta Retórica que Responde</strong>
        <em id="inspQuestion">—</em>
      </div>

      <!-- Respuesta a la Novedad para Elsevier -->
      <div class="inspector-meta-block">
        <strong>🎯 Respuesta a la Novedad (Elsevier BSPC)</strong>
        <span id="inspNovelty">—</span>
      </div>

      <!-- Métrica Cuantitativa -->
      <div class="inspector-meta-block">
        <strong>⚡ Métrica / Hecho Cuantitativo</strong>
        <span id="inspMetrics">—</span>
      </div>

      <!-- Sustento en la Tesis de Julián -->
      <div class="inspector-meta-block">
        <strong>📖 Sustento en la Tesis de Maestría de Julián</strong>
        <span id="inspThesis">—</span>
      </div>

      <!-- Bloques Canónicos y Ubicación -->
      <div class="inspector-meta-block">
        <strong>📑 Bloques Canónicos y Ubicación</strong>
        <div style="font-size: 11px; color: #94a3b8; margin-bottom: 4px;" id="inspLocation">—</div>
        <div class="inspector-blocks" id="inspBlocks"></div>
      </div>

      <button class="btn-action-jump" id="btnJumpPdf" onclick="jumpToPaperPreview()">
        📄 Ir a esta Sección en el Visor PDF (<span id="inspPdfPage">Pág. 1</span>) ↗
      </button>
    </aside>
  </div>

  <script>
    const graphData = {graph_json};

    let isRotating = true;
    let selectedNode = null;
    let activeGroup = null;
    let hoverNode = null;
    let targetPdfPage = 1;
    let wheelMode = 'zoom'; // 'zoom' | 'page'

    const highlightNodes = new Set();
    const highlightLinks = new Set();

    const elem = document.getElementById('3d-graph');
    const Graph = ForceGraph3D()(elem)
      .graphData(graphData)
      .backgroundColor('#0a0a10')
      .showNavInfo(false)
      .nodeLabel(node => `${{node.label}} [${{node.category}}]`)
      .nodeVal(node => node.size || 5)
      .nodeResolution(24)
      .nodeColor(node => {{
        if (highlightNodes.size > 0 && !highlightNodes.has(node.id)) {{
          return 'rgba(45, 52, 75, 0.22)';
        }}
        return node.color || '#38bdf8';
      }})
      .linkWidth(link => {{
        if (highlightLinks.size > 0 && !highlightLinks.has(link)) return 0.5;
        return link.value ? link.value * 0.7 : 1.2;
      }})
      .linkColor(link => {{
        if (highlightLinks.size > 0 && !highlightLinks.has(link)) {{
          return 'rgba(25, 30, 48, 0.08)';
        }}
        if (link.source && (link.source.group === 'novelty' || link.source === 'novelty')) return 'rgba(16, 185, 129, 0.55)';
        if (link.source && (link.source.group === 'problem' || link.source === 'problem')) return 'rgba(244, 63, 94, 0.45)';
        return 'rgba(56, 189, 248, 0.35)';
      }})
      .linkDirectionalParticles(2)
      .linkDirectionalParticleWidth(link => {{
        if (highlightLinks.size > 0 && !highlightLinks.has(link)) return 0;
        return 1.6;
      }})
      .linkDirectionalParticleSpeed(0.005)
      .linkDirectionalParticleColor(link => {{
        if (link.source && (link.source.group === 'novelty' || link.source === 'novelty')) return '#10b981';
        if (link.source && (link.source.group === 'problem' || link.source === 'problem')) return '#f43f5e';
        return '#38bdf8';
      }})
      .linkLabel(link => link.label)
      .onNodeHover(node => {{
        elem.style.cursor = node ? 'pointer' : null;
        hoverNode = node;
        updateHighlight();
        Graph.nodeColor(Graph.nodeColor()).linkColor(Graph.linkColor()).linkWidth(Graph.linkWidth());
      }})
      .onNodeClick(node => {{
        selectNode(node);
      }})
      .onBackgroundClick(() => {{
        closeInspector();
      }});

    // Configure OrbitControls for maximum responsiveness, buttery smooth damping, and non-blocking auto-rotate
    setTimeout(() => {{
      const controls = Graph.controls();
      if (controls) {{
        controls.enableDamping = true;
        controls.dampingFactor = 0.08;
        controls.rotateSpeed = 0.85;
        controls.zoomSpeed = 1.35;
        controls.panSpeed = 0.85;
        controls.enableZoom = true;
        controls.autoRotate = isRotating;
        controls.autoRotateSpeed = 0.7;

        // Yield auto-rotation gently when user starts manipulating
        controls.addEventListener('start', () => {{
          if (isRotating) {{
            controls.autoRotate = false;
          }}
        }});
        controls.addEventListener('end', () => {{
          if (isRotating && !selectedNode) {{
            controls.autoRotate = true;
          }}
        }});
      }}
    }}, 200);

    function updateHighlight() {{
      highlightNodes.clear();
      highlightLinks.clear();

      if (hoverNode) {{
        highlightNodes.add(hoverNode.id);
        graphData.links.forEach(l => {{
          const sId = typeof l.source === 'object' ? l.source.id : l.source;
          const tId = typeof l.target === 'object' ? l.target.id : l.target;
          if (sId === hoverNode.id || tId === hoverNode.id) {{
            highlightLinks.add(l);
            highlightNodes.add(sId);
            highlightNodes.add(tId);
          }}
        }});
      }} else if (activeGroup) {{
        graphData.nodes.forEach(n => {{
          if (n.group === activeGroup || n.group === 'core') {{
            highlightNodes.add(n.id);
          }}
        }});
        graphData.links.forEach(l => {{
          const sId = typeof l.source === 'object' ? l.source.id : l.source;
          const tId = typeof l.target === 'object' ? l.target.id : l.target;
          if (highlightNodes.has(sId) && highlightNodes.has(tId)) {{
            highlightLinks.add(l);
          }}
        }});
      }}
    }}

    function toggleRotate() {{
      isRotating = !isRotating;
      const controls = Graph.controls();
      if (controls) {{
        controls.autoRotate = isRotating;
      }}
      const btn = document.getElementById('btnAutoRotate');
      btn.innerHTML = isRotating ? '⏸️ Pausar giro' : '▶️ Reanudar giro';
      btn.classList.toggle('active', isRotating);
    }}
    document.getElementById('btnAutoRotate').addEventListener('click', toggleRotate);

    function toggleWheelMode() {{
      wheelMode = (wheelMode === 'zoom') ? 'page' : 'zoom';
      const btn = document.getElementById('btnWheelMode');
      btn.innerHTML = wheelMode === 'zoom' ? '🖱️ Rueda: Zoom 3D' : '📜 Rueda: Scroll Página';
      btn.classList.toggle('active', wheelMode === 'page');
    }}
    document.getElementById('btnWheelMode').addEventListener('click', toggleWheelMode);

    // Mouse wheel delegate: forward to parent page scroll when hovering UI, holding Shift, or in page scroll mode
    window.addEventListener('wheel', (e) => {{
      const isUI = e.target.closest('#famlegend, #rellegend, #toolbar, h1, #panel, .inspector-card');
      if (wheelMode === 'page' || e.shiftKey || isUI) {{
        if (window.parent && window.parent !== window) {{
          window.parent.postMessage({{ type: 'page_scroll', deltaY: e.deltaY }}, '*');
        }}
      }}
    }}, {{ passive: true }});

    document.getElementById('zoomin').addEventListener('click', () => {{
      const pos = Graph.cameraPosition();
      Graph.cameraPosition({{ x: pos.x * 0.72, y: pos.y * 0.72, z: pos.z * 0.72 }}, null, 350);
    }});

    document.getElementById('zoomout').addEventListener('click', () => {{
      const pos = Graph.cameraPosition();
      Graph.cameraPosition({{ x: pos.x * 1.35, y: pos.y * 1.35, z: pos.z * 1.35 }}, null, 350);
    }});

    document.getElementById('zoomreset').addEventListener('click', () => {{
      isRotating = true;
      const controls = Graph.controls();
      if (controls) controls.autoRotate = true;
      document.getElementById('btnAutoRotate').innerHTML = '⏸️ Pausar giro';
      document.getElementById('btnAutoRotate').classList.add('active');
      activeGroup = null;
      document.querySelectorAll('.famchip').forEach(c => {{
        c.classList.remove('on');
        c.style.background = '#14172a';
        c.style.color = '#e4e4ed';
      }});
      updateHighlight();
      Graph.nodeColor(Graph.nodeColor()).linkColor(Graph.linkColor()).linkWidth(Graph.linkWidth());
      Graph.cameraPosition({{ x: 0, y: 30, z: 420 }}, {{ x: 0, y: 0, z: 0 }}, 800);
    }});

    function selectNode(node) {{
      selectedNode = node;
      const controls = Graph.controls();
      if (controls) controls.autoRotate = false;

      const dist = 160;
      Graph.cameraPosition(
        {{ x: node.x + dist * 0.7, y: node.y + dist * 0.35, z: node.z + dist * 0.7 }},
        {{ x: node.x, y: node.y, z: node.z }},
        900
      );

      const card = document.getElementById('inspectorCard');
      card.style.display = 'block';
      
      const badge = document.getElementById('inspBadge');
      badge.textContent = node.badge || node.category;
      badge.style.background = `${{node.color}}25`;
      badge.style.color = node.color;
      badge.style.border = `1px solid ${{node.color}}`;

      document.getElementById('inspTitle').textContent = node.label;
      document.getElementById('inspDesc').textContent = node.desc;
      document.getElementById('inspMetrics').textContent = node.metrics || '—';
      document.getElementById('inspNovelty').textContent = node.novelty_claim || '—';
      document.getElementById('inspThesis').textContent = node.thesis_ref || 'Tesis de Maestría';

      const paraBox = document.getElementById('inspParagraphBox');
      const paraText = document.getElementById('inspParagraphText');
      if (node.paragraph_text) {{
        paraBox.style.display = 'block';
        paraText.textContent = `"${{node.paragraph_text}}"`;
      }} else {{
        paraBox.style.display = 'none';
      }}

      const qBox = document.getElementById('inspQuestionBox');
      const qText = document.getElementById('inspQuestion');
      if (node.rhetorical_question) {{
        qBox.style.display = 'block';
        qText.textContent = `"${{node.rhetorical_question}}"`;
      }} else {{
        qBox.style.display = 'none';
      }}

      targetPdfPage = node.pdf_page || 1;
      document.getElementById('inspPdfPage').textContent = `Pág. ${{targetPdfPage}}`;
      document.getElementById('inspLocation').textContent = `${{node.section_ref || 'Manuscrito'}} · Ubicación en documento: Página ${{targetPdfPage}}`;

      const blocksContainer = document.getElementById('inspBlocks');
      blocksContainer.innerHTML = '';
      (node.paper_blocks || []).forEach(b => {{
        const pill = document.createElement('span');
        pill.className = 'block-pill';
        pill.textContent = b;
        blocksContainer.appendChild(pill);
      }});
    }}

    function closeInspector() {{
      document.getElementById('inspectorCard').style.display = 'none';
      selectedNode = null;
      const controls = Graph.controls();
      if (controls && isRotating) {{
        controls.autoRotate = true;
      }}
    }}

    // Build Family Legend Chips (Exact 8 Pillars matching the User Specification)
    const GROUPS_META = [
      {{ id: 'core', label: {core_label}, color: '#38bdf8' }},
      {{ id: 'app', label: '1. Aplicaciones', color: '#0ea5e9' }},
      {{ id: 'problem', label: '2. Problema Central', color: '#f43f5e' }},
      {{ id: 'sota', label: '3. Ideas SOTA cercanas', color: '#fb7185' }},
      {{ id: 'novelty', label: '4. Novedad', color: '#10b981' }},
      {{ id: 'dataset', label: '5. Datasets Probados', color: '#a855f7' }},
      {{ id: 'eval', label: '6. Métricas & Comparación', color: '#eab308' }},
      {{ id: 'conclusion', label: '7. Conclusiones', color: '#06b6d4' }},
      {{ id: 'future', label: '8. Trabajo Futuro', color: '#ec4899' }}
    ];

    const chipsContainer = document.getElementById('famchips');
    GROUPS_META.forEach(g => {{
      const count = graphData.nodes.filter(n => n.group === g.id).length;
      if (count === 0) return;
      const chip = document.createElement('span');
      chip.className = 'famchip';
      chip.dataset.group = g.id;
      chip.style.borderColor = g.color;
      chip.innerHTML = `<span class="famchip-dot" style="background:${{g.color}}"></span>${{g.label}} (${{count}})`;
      
      chip.addEventListener('click', () => {{
        if (activeGroup === g.id) {{
          activeGroup = null;
          chip.classList.remove('on');
          chip.style.background = '#14172a';
          chip.style.color = '#e4e4ed';
        }} else {{
          activeGroup = g.id;
          document.querySelectorAll('.famchip').forEach(c => {{
            c.classList.remove('on');
            c.style.background = '#14172a';
            c.style.color = '#e4e4ed';
          }});
          chip.classList.add('on');
          chip.style.background = g.color;
          chip.style.color = '#0a0a10';
        }}
        updateHighlight();
        Graph.nodeColor(Graph.nodeColor()).linkColor(Graph.linkColor()).linkWidth(Graph.linkWidth());
      }});

      chipsContainer.appendChild(chip);
    }});

    function searchNodes(query) {{
      if (!query || !query.trim()) {{
        activeGroup = null;
        updateHighlight();
        Graph.nodeColor(Graph.nodeColor()).linkColor(Graph.linkColor()).linkWidth(Graph.linkWidth());
        return;
      }}
      const q = query.toLowerCase().trim();
      const match = graphData.nodes.find(n => 
        n.label.toLowerCase().includes(q) ||
        (n.desc && n.desc.toLowerCase().includes(q)) ||
        (n.paragraph_text && n.paragraph_text.toLowerCase().includes(q)) ||
        (n.metrics && n.metrics.toLowerCase().includes(q)) ||
        (n.novelty_claim && n.novelty_claim.toLowerCase().includes(q))
      );
      if (match) {{
        selectNode(match);
      }}
    }}

    function jumpToPaperPreview() {{
      if (window.parent && window.parent.jumpToPdfPage) {{
        window.parent.jumpToPdfPage(targetPdfPage);
      }} else if (window.parent && window.parent.navigateTab) {{
        window.parent.navigateTab('preview');
      }} else {{
        window.open('/#preview', '_blank');
      }}
    }}
  </script>
</body>
</html>"""
