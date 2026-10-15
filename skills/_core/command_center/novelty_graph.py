"""3D Semantic Knowledge Graph for the MONEEG Scientific Manuscript.

Visualizes the core novelty, state-of-the-art gaps, embedded hardware pillars,
empirical thesis evidence, and Elsevier manuscript sections with their
interconnections and argumentative roles.
"""

from __future__ import annotations

import json
from typing import Any

NOVELTY_GRAPH_DATA: dict[str, Any] = {
    "title": "Grafo 3D de Novedad e Ideas del Manuscrito MONEEG",
    "target_journal": "Elsevier Biomedical Signal Processing and Control",
    "authors": "Julián David Parias Osorio & Andrés Álvarez",
    "project": "Minciencias-92056",
    "summary": "Mapeo topológico de la novedad científica: cómo la arquitectura de hardware embebida y la inyección determinista de marcas resuelven las brechas del SOTA y se sustentan en la evidencia experimental de la tesis.",
    "nodes": [
        # --- 1. CORE NOVELTY NODE ---
        {
            "id": "core-moneeg",
            "label": "MONEEG: Open-Access 32-Ch BCI",
            "group": "core",
            "color": "#38bdf8",
            "size": 24,
            "category": "Novedad Central",
            "badge": "ARQUITECTURA PRINCIPAL",
            "desc": "Framework embebido de adquisición de EEG de 32 canales con sincronización hardware determinista (<5 µs) y piso de ruido submicrovoltio (<1.1 µVpp) optimizado para monitoreo cognitivo pediátrico.",
            "metrics": "32 Canales, 24 bits, ADC Σ-Δ, 250 Hz, <1.1 µVpp, latencia <5 µs, 0% pérdida en 400 min.",
            "novelty_claim": "Supera la disyuntiva entre amplificadores clínicos inaccesibles/pesados y cascos comerciales ruidosos con jitter temporal severo.",
            "thesis_ref": "Capítulo 3 (Diseño Hardware y Firmware), Tesis J. Parias",
            "paper_blocks": ["title-and-keywords.title", "abstract.slot-3", "introduction.block-3"]
        },

        # --- 2. SOTA GAPS (CRIMSON) ---
        {
            "id": "gap-jitter",
            "label": "Brecha: Jitter Temporal (10–50 ms)",
            "group": "gap",
            "color": "#f43f5e",
            "size": 15,
            "category": "Brecha SOTA",
            "badge": "LIMITACIÓN ACTUAL",
            "desc": "En sistemas abiertos convencionales (LSL, UDP por sockets de SO), el búfer de red y la planificación de tareas introducen un jitter aleatorio de 10 a 50 ms que atenúa el P300 más de un 40%.",
            "metrics": "18.5 ± 6.2 ms de dispersión en streaming convencional.",
            "novelty_claim": "Impide el promediado coherente de potenciales evocados en tareas de alta frecuencia.",
            "thesis_ref": "Capítulo 2 (Marco Teórico y Estado del Arte), pág. 24",
            "paper_blocks": ["abstract.slot-2", "introduction.block-2", "related-work.rw-problem-blocks"]
        },
        {
            "id": "gap-noise",
            "label": "Brecha: Piso de Ruido Elevado (>5 µVpp)",
            "group": "gap",
            "color": "#f43f5e",
            "size": 14,
            "category": "Brecha SOTA",
            "badge": "LIMITACIÓN ACTUAL",
            "desc": "Los dispositivos de bajo costo carecen de front-ends analógicos de bajo ruido y planos de masa aislados, produciendo ruidos de fondo >5 µVpp que enmascaran microvoltios de respuesta biológica.",
            "metrics": "Ruido >5 µVpp en headsets de consumo (OpenBCI daisy: ~1.5 µVpp; EEGNet MCU: ~3.0 µVpp).",
            "novelty_claim": "MONEEG garantiza <1.1 µVpp con Sigma = 0.14 µV.",
            "thesis_ref": "Capítulo 4 (Resultados de Banco de Pruebas), pág. 62",
            "paper_blocks": ["abstract.slot-2", "introduction.block-2", "related-work.rw-panorama"]
        },
        {
            "id": "gap-pediatric",
            "label": "Brecha: Ergonomía Pediátrica Rígida",
            "group": "gap",
            "color": "#f43f5e",
            "size": 14,
            "category": "Brecha SOTA",
            "badge": "LIMITACIÓN ACTUAL",
            "desc": "Los gorros clínicos comerciales con cables atados a torres de escritorio provocan aversión y movimiento excesivo en niños con TDAH durante sesiones terapéuticas.",
            "metrics": "Circunferencias adultas 56-58 cm vs infantiles 50-54 cm no adaptadas.",
            "novelty_claim": "Casco modular 3D liviano impreso en filamento flexible con adaptación geométrica pediátrica.",
            "thesis_ref": "Capítulo 3 (Diseño Mecánico y Ensamble 3D), pág. 45",
            "paper_blocks": ["abstract.slot-4", "introduction.block-1", "materials-and-methods.mm-proposal"]
        },
        {
            "id": "gap-preemption",
            "label": "Brecha: Desborde en Arquitecturas Mononúcleo",
            "group": "gap",
            "color": "#f43f5e",
            "size": 13,
            "category": "Brecha SOTA",
            "badge": "LIMITACIÓN ACTUAL",
            "desc": "Sistemas como BEATS (2022) manejan Wi-Fi y adquisición en un único MCU, donde la pila de red puede desalojar o retardar la atención de interrupciones críticas del ADC.",
            "metrics": "Pérdida de paquetes bajo ráfagas intensas de red en microcontroladores no optimizados.",
            "novelty_claim": "Firmware bare-metal optimizado con DMA y ensamblaje de cabecera atómico.",
            "thesis_ref": "Capítulo 3 (Implementación de Firmware en TM4C1294), pág. 52",
            "paper_blocks": ["related-work.rw-panorama", "materials-and-methods.mm-borrowed-machinery"]
        },

        # --- 3. EMBEDDED ARCHITECTURE PILLARS (EMERALD) ---
        {
            "id": "arch-daisychain",
            "label": "Topología: 4x ADS1299 Cascaded SPI",
            "group": "arch",
            "color": "#10b981",
            "size": 17,
            "category": "Pilar Hardware",
            "badge": "INGENIERÍA EMBEBIDA",
            "desc": "Cuatro front-ends ADS1299 en cascada daisy-chain leyendo 32 canales sincrónicos (96 bytes) en una única transacción DMA activada por la línea física DRDY.",
            "metrics": "32 CH simultáneos, 24 bits Σ-Δ, PGA 1x-24x, Zin > 1 GΩ.",
            "novelty_claim": "Permite máxima densidad de canales sin multiplicar buses SPI ni introducir desfase de muestreo entre canales.",
            "thesis_ref": "Capítulo 3 (Sección 3.2: Arreglo de Front-Ends Analógicos), Fig. 3.4",
            "paper_blocks": ["abstract.slot-4", "materials-and-methods.mm-borrowed-machinery"]
        },
        {
            "id": "arch-mcu",
            "label": "Núcleo: ARM Cortex-M4F (120 MHz)",
            "group": "arch",
            "color": "#10b981",
            "size": 16,
            "category": "Pilar Hardware",
            "badge": "INGENIERÍA EMBEBIDA",
            "desc": "Microcontrolador Texas Instruments TM4C1294 operando con firmware bare-metal sin sistema operativo de propósito general para erradicar jitter de scheduler.",
            "metrics": "120 MHz, FPU hardware, SSI sincrónico con DMA uDMA circular.",
            "novelty_claim": "Tiempo de respuesta a interrupción determinista < 1 µs.",
            "thesis_ref": "Capítulo 3 (Sección 3.3: Microcontrolador TM4C1294), pág. 48",
            "paper_blocks": ["materials-and-methods.mm-borrowed-machinery", "materials-and-methods.mm-proposal"]
        },
        {
            "id": "arch-trigger",
            "label": "Mecanismo: Hardware Trigger Injection",
            "group": "arch",
            "color": "#10b981",
            "size": 18,
            "category": "Pilar Hardware",
            "badge": "NOVEDAD CLAVE",
            "desc": "Inyección directa de marcas de eventos mediante interrupción externa GPIO que estampa flags en los 3 bytes de cabecera de la trama SPI en el microsegundo exacto de la conversión.",
            "metrics": "Latencia de enganche de evento 2.4 µs (Std = 0.35 µs).",
            "novelty_claim": "Elimina totalmente el desfase y jitter de los protocolos de red tradicionales.",
            "thesis_ref": "Capítulo 3 (Sección 3.4: Sincronización Temporal de Eventos), pág. 55",
            "paper_blocks": ["abstract.slot-4", "abstract.slot-6", "introduction.block-3", "materials-and-methods.mm-proposal"]
        },
        {
            "id": "arch-power",
            "label": "Aislamiento Galvánico & LDOs de Bajo Ruido",
            "group": "arch",
            "color": "#10b981",
            "size": 15,
            "category": "Pilar Hardware",
            "badge": "INGENIERÍA EMBEBIDA",
            "desc": "Planos de masa analógico y digital separados con unión en estrella; conversores DC-DC aislados con post-regulación lineal ultra-limpia (TPS7A49/TPS7A30 para rieles ±2.5V).",
            "metrics": "PSRR > 80 dB a 100 kHz, rechazo a ruido de batería y RF.",
            "novelty_claim": "Garantiza inmunidad contra emisiones electromagnéticas de transceptores inalámbricos.",
            "thesis_ref": "Capítulo 3 (Sección 3.1: Etapa de Alimentación y Aislamiento), pág. 40",
            "paper_blocks": ["materials-and-methods.mm-proposal"]
        },
        {
            "id": "arch-cap",
            "label": "Casco Pediátrico 3D Ergonómico",
            "group": "arch",
            "color": "#10b981",
            "size": 15,
            "category": "Pilar Hardware",
            "badge": "DISEÑO BIOMÉDICO",
            "desc": "Estructura modular impresa en 3D en poliuretano termoplástico (TPU) con monturas articuladas para electrodos Ag/AgCl y verificación continua de impedancia en tiempo real.",
            "metrics": "Z < 10 kΩ, peso total < 220 g con batería integrada LiPo de 1200 mAh.",
            "novelty_claim": "Comodidad comprobada en infantes sin fatiga ni desplazamiento por tracción de cables.",
            "thesis_ref": "Capítulo 3 (Sección 3.5: Diseño y Fabricación del Casco 3D), pág. 58",
            "paper_blocks": ["abstract.slot-4", "introduction.block-4b", "materials-and-methods.mm-proposal"]
        },

        # --- 4. THESIS EXPERIMENTAL EVIDENCE (PURPLE) ---
        {
            "id": "eval-noise",
            "label": "Evidencia: Ruido <1.1 µVpp (32 Canales)",
            "group": "eval",
            "color": "#a855f7",
            "size": 18,
            "category": "Evidencia Experimental",
            "badge": "GROUND-TRUTH BANCO",
            "desc": "Caracterización de banco con entradas referidas a masa (50 Ω): media Vpp = 0.94 µV, Sigma = 0.14 µV, Vrms ≈ 0.16 µV en toda la matriz de 32 canales.",
            "metrics": "Vpp < 1.1 µV (0.16–70 Hz), relación señal a ruido > 95 dB.",
            "novelty_claim": "Demuestra fidelidad de grado clínico a una fracción del costo comercial.",
            "thesis_ref": "Capítulo 4 (Sección 4.1: Caracterización de Ruido de Entrada), Fig. 4.3",
            "paper_blocks": ["abstract.slot-5", "results-and-discussion.rd-general-task"]
        },
        {
            "id": "eval-endurance",
            "label": "Evidencia: 400 Min Streaming 0% Pérdida",
            "group": "eval",
            "color": "#a855f7",
            "size": 16,
            "category": "Evidencia Experimental",
            "badge": "GROUND-TRUTH BANCO",
            "desc": "Ensayo de fatiga continua durante 400 minutos transmitiendo 14.4 millones de muestras sin un solo paquete descartado ni desbordamiento de FIFO.",
            "metrics": "1.44 x 10^7 muestras adquiridas, jitter entre muestras < 25 µs.",
            "novelty_claim": "Estabilidad requerida para intervenciones clínicas y sesiones terapéuticas prolongadas.",
            "thesis_ref": "Capítulo 4 (Sección 4.2: Evaluación de Pérdida de Paquetes), Fig. 4.6",
            "paper_blocks": ["abstract.slot-5", "results-and-discussion.rd-contribution-blocks"]
        },
        {
            "id": "eval-latency",
            "label": "Evidencia: Jitter Hardware 2.4 µs ± 0.35 µs",
            "group": "eval",
            "color": "#a855f7",
            "size": 17,
            "category": "Evidencia Experimental",
            "badge": "GROUND-TRUTH BANCO",
            "desc": "Medición con analizador lógico digital entre flanco de disparo TTL y estampado en cabecera SPI. Latencia media de 2.4 µs con desviación estándar de 0.35 µs.",
            "metrics": "2.4 µs vs 18.5 ms de LSL por software (>7,000x más preciso).",
            "novelty_claim": "Habilita la sincronización perfecta de ERPs de latencia temprana (N200/P300).",
            "thesis_ref": "Capítulo 4 (Sección 4.3: Medición de Latencia y Jitter Temporal), Fig. 4.9",
            "paper_blocks": ["abstract.slot-6", "results-and-discussion.rd-contribution-blocks"]
        },
        {
            "id": "eval-berger",
            "label": "Evidencia: Bloqueo Alfa de Berger (3.8 dB SNR)",
            "group": "eval",
            "color": "#a855f7",
            "size": 17,
            "category": "Evidencia Experimental",
            "badge": "GROUND-TRUTH FISIOLÓGICO",
            "desc": "Validación in-vivo en reposo con protocolo ojos abiertos vs ojos cerrados en electrodo occipital O2. Atenuación clara del ritmo alfa (8–13 Hz) con incremento de 3.8 dB al cerrar ojos.",
            "metrics": "SNR alfa 3.8 dB, comprobación biológica de ground-truth.",
            "novelty_claim": "Verifica que el hardware captura dinámica electrofisiológica cortical real con alta relación señal-ruido.",
            "thesis_ref": "Capítulo 4 (Sección 4.4: Validación In-Vivo Efecto Berger), Fig. 4.12",
            "paper_blocks": ["abstract.slot-5", "results-and-discussion.rd-cost"]
        },
        {
            "id": "eval-game",
            "label": "Evidencia: Videojuego 'Eagle Eye' en Unity",
            "group": "eval",
            "color": "#a855f7",
            "size": 15,
            "category": "Evidencia Experimental",
            "badge": "VALIDACIÓN COGNITIVA",
            "desc": "Integración del videojuego de atención selectiva Eagle Eye con envío de eventos sincronizados para entrenamiento de control inhibitorio en TDAH.",
            "metrics": "Disparo de estímulo Go/No-Go sincronizado a nivel de microsegundo.",
            "novelty_claim": "Demuestra la aplicabilidad clínica en neurorrehabilitación lúdica pediátrica.",
            "thesis_ref": "Capítulo 3 (Sección 3.6: Integración con Videojuego Serio), pág. 60",
            "paper_blocks": ["introduction.block-3", "results-and-discussion.rd-contribution-blocks"]
        },

        # --- 5. ELSEVIER MANUSCRIPT SECTIONS (SAPPHIRE) ---
        {
            "id": "sec-intro",
            "label": "Sección 1: Inception & Hipótesis",
            "group": "section",
            "color": "#0ea5e9",
            "size": 15,
            "category": "Sección Manuscrito",
            "badge": "PÁGS. 1–3",
            "desc": "Plantea el reto clínico pediátrico en TDAH, la hoja de ruta metodológica de 4 fases y las 3 hipótesis comprobables H1, H2 y H3.",
            "metrics": "Bloques introduction.block-1 al block-6.",
            "novelty_claim": "Fija las preguntas de investigación que gobiernan el manuscrito.",
            "thesis_ref": "Insumo: Introducción y Justificación de la Tesis",
            "paper_blocks": ["introduction.block-1", "introduction.block-4a", "introduction.block-2", "introduction.block-3", "introduction.block-4b", "introduction.block-5", "introduction.block-6"]
        },
        {
            "id": "sec-rw",
            "label": "Sección 2: SOTA & Taxonomía Comparativa",
            "group": "section",
            "color": "#0ea5e9",
            "size": 15,
            "category": "Sección Manuscrito",
            "badge": "PÁGS. 3–4",
            "desc": "Contrasta 18 sistemas contemporáneos en una tabla de síntesis (OpenBCI, BEATS, EEGNet MCU, BioSemi) evidenciando la falta de sincronización hardware pediátrica.",
            "metrics": "Tabla tab:sota_comparison, 18 referencias citadas.",
            "novelty_claim": "Posiciona a MONEEG en un cuadrante único de alta densidad + bajo ruido + sincronización determinista.",
            "thesis_ref": "Insumo: Estado del Arte de la Tesis + Atlas 3D",
            "paper_blocks": ["related-work.rw-preamble", "related-work.rw-panorama", "related-work.rw-problem-blocks", "related-work.rw-closing", "related-work.rw-synthesis-artefact"]
        },
        {
            "id": "sec-methods",
            "label": "Sección 3: Materiales & Arquitectura Embebida",
            "group": "section",
            "color": "#0ea5e9",
            "size": 15,
            "category": "Sección Manuscrito",
            "badge": "PÁGS. 4–5",
            "desc": "Describe formalmente el arreglo daisy-chain de 4x ADS1299, el MCU TM4C1294, los rieles de potencia aislados y el casco modular 3D.",
            "metrics": "Figuras fig:hw_arch y fig:daisychain.",
            "novelty_claim": "Detalla el diseño esquemático y las decisiones de ingeniería para reproducibilidad abierta.",
            "thesis_ref": "Insumo: Capítulo 3 de la Tesis",
            "paper_blocks": ["materials-and-methods.mm-preamble", "materials-and-methods.mm-borrowed-machinery", "materials-and-methods.mm-proposal"]
        },
        {
            "id": "sec-setup",
            "label": "Sección 4: Protocolos Experimentales de Banco",
            "group": "section",
            "color": "#0ea5e9",
            "size": 14,
            "category": "Sección Manuscrito",
            "badge": "PÁG. 5",
            "desc": "Define el generador de calibración con divisor 1000:1 (5–500 µV), analizador lógico digital y el protocolo de reposo de Berger.",
            "metrics": "Tasa de muestreo 250 Hz, tramas UDP de 104 bytes.",
            "novelty_claim": "Rigor metodológico exigido por revisores de instrumentación biomédica.",
            "thesis_ref": "Insumo: Capítulo 4 de la Tesis (Protocolos)",
            "paper_blocks": ["experimental-setup.es-preamble", "experimental-setup.es-dataset", "experimental-setup.es-assessment", "experimental-setup.es-training-details"]
        },
        {
            "id": "sec-results",
            "label": "Sección 5: Resultados & Discusión",
            "group": "section",
            "color": "#0ea5e9",
            "size": 16,
            "category": "Sección Manuscrito",
            "badge": "PÁGS. 6–7",
            "desc": "Presenta el piso de ruido submicrovoltio (<1.1 µVpp), la prueba de 400 minutos sin pérdidas, la latencia de 2.4 µs y el espectrograma O2 del efecto Berger.",
            "metrics": "Figuras fig:noise, fig:loss, fig:latency, fig:berger, fig:events.",
            "novelty_claim": "Confirmación empírica indisputable de las tres hipótesis principales.",
            "thesis_ref": "Insumo: Capítulo 4 de la Tesis (Resultados)",
            "paper_blocks": ["results-and-discussion.rd-general-task", "results-and-discussion.rd-contribution-blocks", "results-and-discussion.rd-cost"]
        },
        {
            "id": "sec-limitations",
            "label": "Sección 6: Limitaciones & Traslación Clínica",
            "group": "section",
            "color": "#0ea5e9",
            "size": 13,
            "category": "Sección Manuscrito",
            "badge": "PÁG. 8",
            "desc": "Reconoce honestamente el consumo de corriente (220 mA, ~4.5h batería), artefactos de movimiento y la necesidad de ensayos a gran escala en niños con TDAH.",
            "metrics": "Batería 1200 mAh, blindaje activo en desarrollo.",
            "novelty_claim": "Blindaje editorial contra rechazo de revisores al admitir límites operativos reales.",
            "thesis_ref": "Insumo: Trabajo Futuro de la Tesis",
            "paper_blocks": ["limitations.lim-opening-concession", "limitations.lim-proposal-items", "limitations.lim-validation-items", "limitations.lim-failure-mode", "limitations.lim-closing"]
        },
        {
            "id": "sec-conclusions",
            "label": "Sección 7: Conclusiones & Ciencia Abierta",
            "group": "section",
            "color": "#0ea5e9",
            "size": 14,
            "category": "Sección Manuscrito",
            "badge": "PÁGS. 8–9",
            "desc": "Sintetiza los 4 aportes fundamentales, anuncia la disponibilidad en código abierto de firmware y hardware bajo Minciencias-92056.",
            "metrics": "Bloques concl-1 al concl-4, CRediT formal.",
            "novelty_claim": "Cierre con impacto científico y traslación a neurotecnología accesible.",
            "thesis_ref": "Insumo: Conclusiones de la Tesis",
            "paper_blocks": ["conclusions.concl-block-1", "conclusions.concl-block-2", "conclusions.concl-block-3", "conclusions.concl-block-4"]
        }
    ],

    "links": [
        # Core to Gaps
        {"source": "core-moneeg", "target": "gap-jitter", "label": "resuelve (sub-5 µs vs 10-50 ms)", "value": 3},
        {"source": "core-moneeg", "target": "gap-noise", "label": "reduce (<1.1 µVpp vs >5 µVpp)", "value": 3},
        {"source": "core-moneeg", "target": "gap-pediatric", "label": "mitiga (casco 3D ergonómico)", "value": 2},
        {"source": "core-moneeg", "target": "gap-preemption", "label": "previene (bare-metal + DMA)", "value": 2},

        # Core to Pillars
        {"source": "core-moneeg", "target": "arch-daisychain", "label": "integra (32 CH sincronizados)", "value": 4},
        {"source": "core-moneeg", "target": "arch-mcu", "label": "ejecuta en (120 MHz determinista)", "value": 3},
        {"source": "core-moneeg", "target": "arch-trigger", "label": "implementa (enganche hardware)", "value": 4},
        {"source": "core-moneeg", "target": "arch-power", "label": "protege con (aislamiento galvánico)", "value": 3},
        {"source": "core-moneeg", "target": "arch-cap", "label": "monta en (impresión flexible 3D)", "value": 2},

        # Pillars to Evidence
        {"source": "arch-daisychain", "target": "eval-noise", "label": "sustenta piso de ruido", "value": 3},
        {"source": "arch-mcu", "target": "eval-endurance", "label": "garantiza cero desbordes", "value": 3},
        {"source": "arch-trigger", "target": "eval-latency", "label": "demuestra 2.4 µs en banco", "value": 4},
        {"source": "arch-trigger", "target": "eval-game", "label": "sincroniza marcas de Unity", "value": 3},
        {"source": "arch-cap", "target": "eval-berger", "label": "mantiene contacto Z < 10 kΩ", "value": 2},
        {"source": "arch-power", "target": "eval-noise", "label": "elimina rizado de fuente", "value": 2},

        # Evidence to Sections
        {"source": "sec-intro", "target": "core-moneeg", "label": "formula hipótesis H1-H3", "value": 3},
        {"source": "sec-rw", "target": "gap-jitter", "label": "analiza estado del arte", "value": 2},
        {"source": "sec-rw", "target": "gap-noise", "label": "compara contra OpenBCI/BEATS", "value": 2},
        {"source": "sec-rw", "target": "gap-preemption", "label": "revisa límites mononúcleo", "value": 2},
        {"source": "sec-methods", "target": "arch-daisychain", "label": "documenta topología SPI", "value": 3},
        {"source": "sec-methods", "target": "arch-mcu", "label": "describe firmware bare-metal", "value": 3},
        {"source": "sec-methods", "target": "arch-trigger", "label": "detalla inyección en cabecera", "value": 4},
        {"source": "sec-methods", "target": "arch-power", "label": "especifica planos analógicos", "value": 2},
        {"source": "sec-methods", "target": "arch-cap", "label": "ilustra casco pediátrico", "value": 2},
        {"source": "sec-setup", "target": "eval-noise", "label": "define prueba con 50 Ω", "value": 3},
        {"source": "sec-setup", "target": "eval-endurance", "label": "define prueba de 400 min", "value": 3},
        {"source": "sec-setup", "target": "eval-latency", "label": "define lógica con osciloscopio", "value": 3},
        {"source": "sec-setup", "target": "eval-berger", "label": "protocolo de reposo O2", "value": 3},
        {"source": "sec-results", "target": "eval-noise", "label": "reporta 0.94 µVpp y curvas", "value": 4},
        {"source": "sec-results", "target": "eval-endurance", "label": "reporta cero paquetes perdidos", "value": 3},
        {"source": "sec-results", "target": "eval-latency", "label": "reporta 2.4 µs determinista", "value": 4},
        {"source": "sec-results", "target": "eval-berger", "label": "reporta 3.8 dB espectrograma", "value": 4},
        {"source": "sec-results", "target": "eval-game", "label": "presenta sincronización Eagle Eye", "value": 3},
        {"source": "sec-limitations", "target": "gap-pediatric", "label": "discute fatiga y artefactos", "value": 2},
        {"source": "sec-conclusions", "target": "core-moneeg", "label": "consolida novedad e impacto", "value": 4}
    ]
}


def build_novelty_graph() -> dict[str, Any]:
    """Return the complete semantic novelty graph for MONEEG."""
    return NOVELTY_GRAPH_DATA


def build_novelty_viewer_html() -> str:
    """Generate the full responsive 3D WebGL viewer for the novelty graph."""
    graph_json = json.dumps(NOVELTY_GRAPH_DATA, ensure_ascii=False)
    
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Grafo 3D de Novedad e Ideas del Manuscrito — MONEEG</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <script src="https://unpkg.com/3d-force-graph@1.73.3/dist/3d-force-graph.min.js"></script>
  <style>
    :root {{
      --bg: #090d16;
      --card-bg: rgba(15, 23, 42, 0.88);
      --border: rgba(56, 189, 248, 0.25);
      --text: #f1f5f9;
      --muted: #94a3b8;
      --cyan: #38bdf8;
      --emerald: #10b981;
      --purple: #a855f7;
      --rose: #f43f5e;
      --blue: #0ea5e9;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      overflow: hidden;
      width: 100vw;
      height: 100vh;
    }}
    #3d-graph {{
      width: 100%;
      height: 100%;
    }}
    /* Topbar HUD */
    .hud-topbar {{
      position: absolute;
      top: 14px;
      left: 14px;
      right: 14px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      pointer-events: none;
      z-index: 10;
    }}
    .hud-title-badge {{
      background: var(--card-bg);
      backdrop-filter: blur(12px);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 10px 16px;
      pointer-events: auto;
      box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    }}
    .hud-title-badge h1 {{
      font-size: 0.95rem;
      font-weight: 700;
      color: var(--cyan);
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .hud-title-badge p {{
      font-size: 0.76rem;
      color: var(--muted);
      margin-top: 2px;
    }}
    .hud-controls {{
      display: flex;
      gap: 8px;
      pointer-events: auto;
      align-items: center;
    }}
    .hud-btn {{
      background: rgba(15, 23, 42, 0.85);
      border: 1px solid var(--border);
      color: var(--text);
      padding: 8px 14px;
      border-radius: 6px;
      font-size: 0.78rem;
      cursor: pointer;
      backdrop-filter: blur(8px);
      transition: all 0.2s;
    }}
    .hud-btn:hover {{
      background: rgba(56, 189, 248, 0.2);
      border-color: var(--cyan);
      color: #fff;
    }}
    .hud-btn.active {{
      background: var(--cyan);
      color: #041226;
      font-weight: 700;
      border-color: var(--cyan);
    }}
    /* Cluster Filter Bar */
    .hud-legend {{
      position: absolute;
      bottom: 16px;
      left: 14px;
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 10px 14px;
      display: flex;
      gap: 14px;
      align-items: center;
      font-size: 0.74rem;
      backdrop-filter: blur(12px);
      z-index: 10;
    }}
    .legend-item {{
      display: flex;
      align-items: center;
      gap: 6px;
      cursor: pointer;
      opacity: 0.9;
    }}
    .legend-item:hover {{ opacity: 1; }}
    .legend-dot {{
      width: 10px;
      height: 10px;
      border-radius: 50%;
      box-shadow: 0 0 8px currentColor;
    }}
    /* Side Inspector Drawer */
    .inspector-card {{
      position: absolute;
      top: 14px;
      right: 14px;
      width: 360px;
      max-height: calc(100vh - 28px);
      overflow-y: auto;
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 18px;
      backdrop-filter: blur(16px);
      box-shadow: 0 12px 40px rgba(0,0,0,0.5);
      display: none;
      z-index: 20;
      animation: slideIn 0.25s ease-out;
    }}
    @keyframes slideIn {{
      from {{ transform: translateX(20px); opacity: 0; }}
      to {{ transform: translateX(0); opacity: 1; }}
    }}
    .inspector-card__header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 12px;
      border-bottom: 1px solid rgba(255,255,255,0.08);
      padding-bottom: 10px;
    }}
    .inspector-badge {{
      display: inline-block;
      font-size: 0.68rem;
      font-weight: 700;
      padding: 3px 8px;
      border-radius: 4px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .inspector-close {{
      background: none;
      border: none;
      color: var(--muted);
      font-size: 1.2rem;
      cursor: pointer;
      padding: 0 4px;
    }}
    .inspector-close:hover {{ color: #fff; }}
    .inspector-title {{
      font-size: 1.05rem;
      font-weight: 700;
      color: #fff;
      margin-bottom: 8px;
      line-height: 1.3;
    }}
    .inspector-desc {{
      font-size: 0.82rem;
      color: var(--muted);
      line-height: 1.5;
      margin-bottom: 14px;
    }}
    .inspector-meta-block {{
      background: rgba(255,255,255,0.04);
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 6px;
      padding: 10px 12px;
      margin-bottom: 10px;
      font-size: 0.78rem;
    }}
    .inspector-meta-block strong {{
      color: var(--cyan);
      display: block;
      margin-bottom: 4px;
      font-size: 0.72rem;
      text-transform: uppercase;
    }}
    .inspector-blocks {{
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
      margin-top: 6px;
    }}
    .block-pill {{
      background: rgba(56, 189, 248, 0.15);
      border: 1px solid rgba(56, 189, 248, 0.3);
      color: var(--cyan);
      padding: 2px 6px;
      border-radius: 3px;
      font-size: 0.68rem;
      font-family: monospace;
    }}
    .btn-action-jump {{
      width: 100%;
      background: linear-gradient(135deg, #0ea5e9, #0284c7);
      color: #fff;
      border: none;
      padding: 8px 12px;
      border-radius: 6px;
      font-size: 0.8rem;
      font-weight: 600;
      cursor: pointer;
      margin-top: 10px;
      transition: opacity 0.2s;
    }}
    .btn-action-jump:hover {{ opacity: 0.9; }}
  </style>
</head>
<body>

  <!-- Topbar HUD -->
  <div class="hud-topbar">
    <div class="hud-title-badge">
      <h1>🕸️ Grafo 3D de Novedad e Ideas del Manuscrito</h1>
      <p>Topología semántica de aportes técnicos, evidencia de banco de la tesis y estructura del paper (Elsevier)</p>
    </div>
    <div class="hud-controls">
      <button class="hud-btn" id="btnAutoRotate" onclick="toggleRotate()">⏸ Pausar Giro</button>
      <button class="hud-btn" onclick="resetCamera()">🎯 Centrar Novedad</button>
      <button class="hud-btn" onclick="filterGroup('all')">Ver Todo</button>
    </div>
  </div>

  <!-- 3D Canvas Container -->
  <div id="3d-graph"></div>

  <!-- Bottom Legend HUD -->
  <div class="hud-legend">
    <div class="legend-item" onclick="filterGroup('core')">
      <span class="legend-dot" style="background: var(--cyan); color: var(--cyan);"></span>
      <span>Novedad Central (MONEEG)</span>
    </div>
    <div class="legend-item" onclick="filterGroup('gap')">
      <span class="legend-dot" style="background: var(--rose); color: var(--rose);"></span>
      <span>Brechas SOTA (Problemas)</span>
    </div>
    <div class="legend-item" onclick="filterGroup('arch')">
      <span class="legend-dot" style="background: var(--emerald); color: var(--emerald);"></span>
      <span>Pilares Embebidos (Hardware)</span>
    </div>
    <div class="legend-item" onclick="filterGroup('eval')">
      <span class="legend-dot" style="background: var(--purple); color: var(--purple);"></span>
      <span>Evidencia Tesis (Ground-Truth)</span>
    </div>
    <div class="legend-item" onclick="filterGroup('section')">
      <span class="legend-dot" style="background: var(--blue); color: var(--blue);"></span>
      <span>Secciones Manuscrito (Elsevier)</span>
    </div>
  </div>

  <!-- Side Inspector Drawer -->
  <aside class="inspector-card" id="inspectorCard">
    <div class="inspector-card__header">
      <span class="inspector-badge" id="inspBadge" style="background: rgba(56,189,248,0.2); color: var(--cyan);">Categoría</span>
      <button class="inspector-close" onclick="closeInspector()">&times;</button>
    </div>
    <div class="inspector-title" id="inspTitle">Nombre del Nodo</div>
    <p class="inspector-desc" id="inspDesc">Descripción detallada del nodo y su rol en la investigación.</p>
    
    <div class="inspector-meta-block">
      <strong>⚡ Métrica / Hecho Cuantitativo</strong>
      <span id="inspMetrics">—</span>
    </div>

    <div class="inspector-meta-block">
      <strong>🎯 Respuesta a la Novedad (Elsevier)</strong>
      <span id="inspNovelty">—</span>
    </div>

    <div class="inspector-meta-block">
      <strong>📖 Sustento en la Tesis de Julián</strong>
      <span id="inspThesis">—</span>
    </div>

    <div class="inspector-meta-block">
      <strong>📑 Bloques Canónicos Vinculados</strong>
      <div class="inspector-blocks" id="inspBlocks"></div>
    </div>

    <button class="btn-action-jump" onclick="jumpToPaperPreview()">📄 Inspeccionar en el Visor PDF</button>
  </aside>

  <script>
    const graphData = {graph_json};

    let isRotating = true;
    let selectedNode = null;
    let currentFilter = 'all';

    const elem = document.getElementById('3d-graph');
    const Graph = ForceGraph3D()(elem)
      .graphData(graphData)
      .backgroundColor('#090d16')
      .showNavInfo(false)
      .nodeLabel(node => `${{node.label}} (${{node.category}})`)
      .nodeColor(node => node.color)
      .nodeVal(node => node.size)
      .nodeResolution(24)
      .linkWidth(link => link.value ? link.value * 0.7 : 1)
      .linkColor(() => 'rgba(56, 189, 248, 0.22)')
      .linkDirectionalParticles(2)
      .linkDirectionalParticleWidth(1.6)
      .linkDirectionalParticleSpeed(0.005)
      .linkDirectionalParticleColor(() => '#38bdf8')
      .linkLabel(link => link.label)
      .onNodeClick(node => {{
        selectNode(node);
      }})
      .onBackgroundClick(() => {{
        closeInspector();
      }});

    // Auto-orbit camera
    let angle = 0;
    const distance = 480;
    setInterval(() => {{
      if (isRotating) {{
        angle += 0.003;
        Graph.cameraPosition({{
          x: distance * Math.sin(angle),
          z: distance * Math.cos(angle)
        }});
      }}
    }}, 20);

    function toggleRotate() {{
      isRotating = !isRotating;
      const btn = document.getElementById('btnAutoRotate');
      btn.textContent = isRotating ? '⏸ Pausar Giro' : '▶ Reanudar Giro';
    }}

    function resetCamera() {{
      isRotating = false;
      document.getElementById('btnAutoRotate').textContent = '▶ Reanudar Giro';
      Graph.cameraPosition({{ x: 0, y: 30, z: 420 }}, {{ x: 0, y: 0, z: 0 }}, 1200);
    }}

    function selectNode(node) {{
      selectedNode = node;
      isRotating = false;
      document.getElementById('btnAutoRotate').textContent = '▶ Reanudar Giro';

      // Focus camera on clicked node
      const dist = 180;
      Graph.cameraPosition(
        {{ x: node.x + dist * 0.7, y: node.y + dist * 0.4, z: node.z + dist * 0.7 }},
        {{ x: node.x, y: node.y, z: node.z }},
        1000
      );

      // Populate inspector
      const card = document.getElementById('inspectorCard');
      card.style.display = 'block';
      
      const badge = document.getElementById('inspBadge');
      badge.textContent = node.badge || node.category;
      badge.style.background = `${{node.color}}22`;
      badge.style.color = node.color;
      badge.style.borderColor = node.color;

      document.getElementById('inspTitle').textContent = node.label;
      document.getElementById('inspDesc').textContent = node.desc;
      document.getElementById('inspMetrics').textContent = node.metrics || '—';
      document.getElementById('inspNovelty').textContent = node.novelty_claim || '—';
      document.getElementById('inspThesis').textContent = node.thesis_ref || 'Tesis de Maestría';

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
    }}

    function filterGroup(group) {{
      currentFilter = group;
      if (group === 'all') {{
        Graph.graphData(graphData);
      }} else {{
        const filteredNodes = graphData.nodes.filter(n => n.group === group || n.id === 'core-moneeg');
        const nodeIds = new Set(filteredNodes.map(n => n.id));
        const filteredLinks = graphData.links.filter(l => 
          nodeIds.has(typeof l.source === 'object' ? l.source.id : l.source) &&
          nodeIds.has(typeof l.target === 'object' ? l.target.id : l.target)
        );
        Graph.graphData({{ nodes: filteredNodes, links: filteredLinks }});
      }}
    }}

    function jumpToPaperPreview() {{
      if (window.parent && window.parent.navigateTab) {{
        window.parent.navigateTab('preview');
      }} else {{
        window.open('/#preview', '_blank');
      }}
    }}
  </script>
</body>
</html>"""
