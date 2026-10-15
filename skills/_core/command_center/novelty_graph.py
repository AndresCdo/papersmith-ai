"""3D Semantic Knowledge Graph for the MONEEG Scientific Manuscript.

Visualizes the core novelty, state-of-the-art gaps, embedded hardware pillars,
empirical thesis evidence, Elsevier manuscript sections, and crucially the
MOST RELEVANT PARAGRAPHS of the paper that articulate its novelty and core findings.
"""

from __future__ import annotations

import json
from typing import Any

NOVELTY_GRAPH_DATA: dict[str, Any] = {
    "title": "Grafo 3D de Novedad e Ideas del Manuscrito MONEEG",
    "target_journal": "Elsevier Biomedical Signal Processing and Control",
    "authors": "Julián David Parias Osorio & Andrés Álvarez",
    "project": "Minciencias-92056",
    "summary": "Mapeo topológico de la novedad científica: cómo los párrafos clave de cada sección defienden la innovación de MONEEG, resuelven las brechas del SOTA y se sustentan en la evidencia experimental de la tesis.",
    "nodes": [
        # =====================================================================
        # 1. CORE NOVELTY NODE (CYAN)
        # =====================================================================
        {
            "id": "core-moneeg",
            "label": "MONEEG: Open-Access 32-Ch BCI",
            "group": "core",
            "color": "#38bdf8",
            "size": 15,
            "category": "Novedad Central",
            "badge": "ARQUITECTURA PRINCIPAL",
            "desc": "Framework embebido de adquisición de EEG de 32 canales con sincronización hardware determinista (<5 µs) y piso de ruido submicrovoltio (<1.1 µVpp) optimizado para monitoreo cognitivo pediátrico.",
            "rhetorical_question": "¿Cuál es la contribución técnica y traslacional definitiva que introduce el artículo frente a los sistemas BCI existentes?",
            "paragraph_text": "MONEEG resolves this bottleneck through a co-designed embedded architecture. By combining a bare-metal 120 MHz ARM Cortex-M4F microcontroller with four cascaded ADS1299 analog front-ends, the platform performs synchronized 24-bit delta-sigma conversion across 32 channels, embedding serious game stimulus trigger flags directly into the SPI transfer frame at the hardware interrupt level.",
            "metrics": "32 Canales, 24 bits, ADC Σ-Δ, 250 Hz, <1.1 µVpp, latencia <5 µs, 0% pérdida en 400 min.",
            "novelty_claim": "Supera la disyuntiva entre amplificadores clínicos inaccesibles/pesados y cascos comerciales ruidosos con jitter temporal severo.",
            "thesis_ref": "Capítulo 3 (Diseño Hardware y Firmware), Tesis J. Parias",
            "pdf_page": 2,
            "section_ref": "Sección 1 (Introducción)",
            "paper_blocks": ["title-and-keywords.title", "abstract.slot-3", "introduction.block-3"]
        },

        # =====================================================================
        # 2. SOTA GAPS (CRIMSON)
        # =====================================================================
        {
            "id": "gap-jitter",
            "label": "Brecha: Jitter Temporal (10–50 ms)",
            "group": "gap",
            "color": "#f43f5e",
            "size": 15,
            "category": "Brecha SOTA",
            "badge": "LIMITACIÓN ACTUAL",
            "desc": "En sistemas abiertos convencionales (LSL, UDP por sockets de SO), el búfer de red y la planificación de tareas introducen un jitter aleatorio de 10 a 50 ms que atenúa el P300 más de un 40%.",
            "rhetorical_question": "¿Por qué el timestamping basado en software en sistemas operativos convencionales destruye la coherencia de potenciales evocados?",
            "paragraph_text": "When stimulus delivery software and data acquisition software run on separate execution loops, network and OS buffering produce random temporal jitter exceeding 30 ms. In ERP averaging, a jitter of this magnitude completely blurs high-frequency components and attenuates the P300 amplitude by more than 40%.",
            "metrics": "18.5 ± 6.2 ms de dispersión en streaming convencional.",
            "novelty_claim": "Impide el promediado coherente de potenciales evocados en tareas de alta frecuencia.",
            "thesis_ref": "Capítulo 2 (Marco Teórico y Estado del Arte), pág. 24",
            "pdf_page": 3,
            "section_ref": "Sección 2 (Related Work)",
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
            "rhetorical_question": "¿Qué limita la sensibilidad de los dispositivos de electroencefalografía abiertos frente a señales corticales sutiles?",
            "paragraph_text": "Furthermore, analog noise floors often exceed 5 µVpp in low-cost headsets, washing out low-amplitude microvolt cortical responses and preventing reliable extraction of single-trial neurocognitive markers.",
            "metrics": "Ruido >5 µVpp en headsets de consumo (OpenBCI daisy: ~1.5 µVpp; EEGNet MCU: ~3.0 µVpp).",
            "novelty_claim": "MONEEG garantiza <1.1 µVpp con Sigma = 0.14 µV.",
            "thesis_ref": "Capítulo 4 (Resultados de Banco de Pruebas), pág. 62",
            "pdf_page": 1,
            "section_ref": "Sección 1 (Introducción)",
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
            "rhetorical_question": "¿Por qué los cascos clínicos estándar fracasan en estudios de neurofeedback pediátrico en TDAH?",
            "paragraph_text": "Standard clinical setups rely on rigid, high-density caps connected via cumbersome tethers to expensive benchtop amplifiers, causing anxiety and behavioral resistance in young subjects. Conversely, low-cost consumer headsets lack channel density and exhibit excessive inter-electrode impedance variance.",
            "metrics": "Circunferencias adultas 56-58 cm vs infantiles 50-54 cm no adaptadas.",
            "novelty_claim": "Casco modular 3D liviano impreso en filamento flexible con adaptación geométrica pediátrica.",
            "thesis_ref": "Capítulo 3 (Diseño Mecánico y Ensamble 3D), pág. 45",
            "pdf_page": 1,
            "section_ref": "Sección 1 (Introducción)",
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
            "rhetorical_question": "¿Cómo vulnera la congestión de la pila de red Wi-Fi la integridad del muestreo biopotencial en MCUs convencionales?",
            "paragraph_text": "Among open-source systems, BEATS represents a notable milestone; however, it utilizes a single-MCU architecture where high-throughput Wi-Fi socket handling can preempt critical time-sensitive ADC servicing under peak network load, leading to unhandled packet drops.",
            "metrics": "Pérdida de paquetes bajo ráfagas intensas de red en microcontroladores no optimizados.",
            "novelty_claim": "Firmware bare-metal optimizado con DMA y ensamblaje de cabecera atómico.",
            "thesis_ref": "Capítulo 3 (Implementación de Firmware en TM4C1294), pág. 52",
            "pdf_page": 3,
            "section_ref": "Sección 2 (Related Work)",
            "paper_blocks": ["related-work.rw-panorama", "materials-and-methods.mm-borrowed-machinery"]
        },

        # =====================================================================
        # 3. EMBEDDED ARCHITECTURE PILLARS (EMERALD)
        # =====================================================================
        {
            "id": "arch-daisychain",
            "label": "Topología: 4x ADS1299 Cascaded SPI",
            "group": "arch",
            "color": "#10b981",
            "size": 17,
            "category": "Pilar Hardware",
            "badge": "INGENIERÍA EMBEBIDA",
            "desc": "Cuatro front-ends ADS1299 en cascada daisy-chain leyendo 32 canales sincrónicos (96 bytes) en una única transacción DMA activada por la línea física DRDY.",
            "rhetorical_question": "¿Cómo se sincronizan y transfieren 32 canales de 24 bits sin introducir skew entre chips ni multiplicar líneas de control?",
            "paragraph_text": "The biopotential acquisition front-end consists of four Texas Instruments ADS1299 integrated circuits connected in a SPI daisy-chain configuration. The cascaded SPI configuration allows the host MCU to read all 32 channels (96 bytes plus status words) in a single synchronous DMA transaction triggered by the data-ready (DRDY) hardware interrupt line.",
            "metrics": "32 CH simultáneos, 24 bits Σ-Δ, PGA 1x-24x, Zin > 1 GΩ.",
            "novelty_claim": "Permite máxima densidad de canales sin multiplicar buses SPI ni introducir desfase de muestreo entre canales.",
            "thesis_ref": "Capítulo 3 (Sección 3.2: Arreglo de Front-Ends Analógicos), Fig. 3.4",
            "pdf_page": 4,
            "section_ref": "Sección 3 (Materiales y Métodos)",
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
            "rhetorical_question": "¿Por qué una implementación bare-metal sin RTOS comercial es necesaria para garantizar determinismo estricto?",
            "paragraph_text": "By executing on a bare-metal 120 MHz ARM Cortex-M4F microcontroller without general-purpose OS layers, task dispatching is strictly governed by deterministic hardware interrupts, ensuring ISR latency under 1 microsecond.",
            "metrics": "120 MHz, FPU hardware, SSI sincrónico con DMA uDMA circular.",
            "novelty_claim": "Tiempo de respuesta a interrupción determinista < 1 µs.",
            "thesis_ref": "Capítulo 3 (Sección 3.3: Microcontrolador TM4C1294), pág. 48",
            "pdf_page": 4,
            "section_ref": "Sección 3 (Materiales y Métodos)",
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
            "rhetorical_question": "¿Cómo se logra sincronización temporal a nivel de microsegundo entre eventos del juego y paquetes EEG?",
            "paragraph_text": "The microcontroller embeds stimulus flags directly into the 3-byte protocol header of each transmission packet via an external GPIO interrupt linked to the serious game engine, stamping event codes at the physical instant of analog-to-digital conversion.",
            "metrics": "Latencia de enganche de evento 2.4 µs (Std = 0.35 µs).",
            "novelty_claim": "Elimina totalmente el desfase y jitter de los protocolos de red tradicionales.",
            "thesis_ref": "Capítulo 3 (Sección 3.4: Sincronización Temporal de Eventos), pág. 55",
            "pdf_page": 5,
            "section_ref": "Sección 3 (Materiales y Métodos)",
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
            "rhetorical_question": "¿Cómo se aísla el plano biopotencial analógico de los picos de conmutación de la antena Wi-Fi y los reguladores conmutados?",
            "paragraph_text": "To decouple noisy digital RF communications from the ultra-sensitive microvolt analog plane, MONEEG features complete galvanic isolation. Separate ground planes are bridged only at a dedicated stellar point, and isolated DC-DC converters deliver clean ±2.5 V analog rails with secondary ultra-low-dropout (LDO) linear regulators (TPS7A49/TPS7A30).",
            "metrics": "PSRR > 80 dB a 100 kHz, rechazo a ruido de batería y RF.",
            "novelty_claim": "Garantiza inmunidad contra emisiones electromagnéticas de transceptores inalámbricos.",
            "thesis_ref": "Capítulo 3 (Sección 3.1: Etapa de Alimentación y Aislamiento), pág. 40",
            "pdf_page": 5,
            "section_ref": "Sección 3 (Materiales y Métodos)",
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
            "rhetorical_question": "¿Cómo se optimiza mecánicamente la interfaz de electrodos para pacientes pediátricos durante sesiones lúdicas?",
            "paragraph_text": "A custom ergonomic 3D pediatric cap with continuous impedance sensing maintains stable contact impedance (Z < 10 kΩ) across the 10-20 international montage without inducing pressure fatigue or mechanical displacement during active video gameplay.",
            "metrics": "Z < 10 kΩ, peso total < 220 g con batería integrada LiPo de 1200 mAh.",
            "novelty_claim": "Comodidad comprobada en infantes sin fatiga ni desplazamiento por tracción de cables.",
            "thesis_ref": "Capítulo 3 (Sección 3.5: Diseño y Fabricación del Casco 3D), pág. 58",
            "pdf_page": 2,
            "section_ref": "Sección 1 (Introducción)",
            "paper_blocks": ["abstract.slot-4", "introduction.block-4b", "materials-and-methods.mm-proposal"]
        },

        # =====================================================================
        # 4. THESIS EXPERIMENTAL EVIDENCE (PURPLE)
        # =====================================================================
        {
            "id": "eval-noise",
            "label": "Evidencia: Ruido <1.1 µVpp (32 Canales)",
            "group": "eval",
            "color": "#a855f7",
            "size": 18,
            "category": "Evidencia Experimental",
            "badge": "GROUND-TRUTH BANCO",
            "desc": "Caracterización de banco con entradas referidas a masa (50 Ω): media Vpp = 0.94 µV, Sigma = 0.14 µV, Vrms ≈ 0.16 µV en toda la matriz de 32 canales.",
            "rhetorical_question": "¿Qué evidencia numérica demuestra que la matriz analógica logra un piso de ruido submicrovoltio?",
            "paragraph_text": "Across all 32 channels, the input-referred noise floor remained strictly under 1.1 µVpp (mean Vpp = 0.94 µV, σ = 0.14 µV, Vrms ≈ 0.16 µV). This is well below the typical amplitude of pediatric scalp EEG (10--100 µV), ensuring that delicate cognitive potentials are preserved without amplifier distortion.",
            "metrics": "Vpp < 1.1 µV (0.16–70 Hz), relación señal a ruido > 95 dB.",
            "novelty_claim": "Demuestra fidelidad de grado clínico a una fracción del costo comercial.",
            "thesis_ref": "Capítulo 4 (Sección 4.1: Caracterización de Ruido de Entrada), Fig. 4.3",
            "pdf_page": 6,
            "section_ref": "Sección 5 (Resultados)",
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
            "rhetorical_question": "¿Cómo se comprobó la confiabilidad y robustez del enlace inalámbrico en sesiones de monitoreo prolongadas?",
            "paragraph_text": "In long-term streaming endurance tests, the system operated continuously for 400 minutes, transmitting 1.44 x 10^7 samples with zero dropped packets and bounded inter-sample jitter (< 25 µs), demonstrating absolute link stability.",
            "metrics": "1.44 x 10^7 muestras adquiridas, jitter entre muestras < 25 µs.",
            "novelty_claim": "Estabilidad requerida para intervenciones clínicas y sesiones terapéuticas prolongadas.",
            "thesis_ref": "Capítulo 4 (Sección 4.2: Evaluación de Pérdida de Paquetes), Fig. 4.6",
            "pdf_page": 6,
            "section_ref": "Sección 5 (Resultados)",
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
            "rhetorical_question": "¿Cuál es la dispersión temporal exacta de la inyección de marcas en comparación con protocolos por software?",
            "paragraph_text": "In hardware synchronization tests, the measured delay between the external TTL stimulus trigger and header latching was 2.4 µs with a standard deviation of 0.35 µs, completely outperforming software LSL streaming pipelines (18.5 ± 6.2 ms).",
            "metrics": "2.4 µs vs 18.5 ms de LSL por software (>7,000x más preciso).",
            "novelty_claim": "Habilita la sincronización perfecta de ERPs de latencia temprana (N200/P300).",
            "thesis_ref": "Capítulo 4 (Sección 4.3: Medición de Latencia y Jitter Temporal), Fig. 4.9",
            "pdf_page": 6,
            "section_ref": "Sección 5 (Resultados)",
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
            "rhetorical_question": "¿Qué prueba fisiológica in-vivo demuestra que MONEEG captura biopotenciales cerebrales reales y no ruido sintético?",
            "paragraph_text": "Recording at the occipital electrode O2 during an eyes-open vs. eyes-closed resting state protocol demonstrated clear Berger alpha rhythm attenuation. During the eyes-closed intervals, spectral power in the 8--13 Hz alpha band increased by 3.8 dB relative to eyes-open, providing indisputable proof of physiological ground-truth capture.",
            "metrics": "SNR alfa 3.8 dB, comprobación biológica de ground-truth.",
            "novelty_claim": "Verifica que el hardware captura dinámica electrofisiológica cortical real con alta relación señal-ruido.",
            "thesis_ref": "Capítulo 4 (Sección 4.4: Validación In-Vivo Efecto Berger), Fig. 4.12",
            "pdf_page": 7,
            "section_ref": "Sección 5 (Resultados)",
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
            "rhetorical_question": "¿Cómo se conecta la plataforma con paradigmas lúdicos de neurorrehabilitación en tiempo real?",
            "paragraph_text": "Stimulus render events from the Unity serious game Eagle Eye trigger a physical interrupt that latches marker codes into the SPI frame header at the exact instant of ADC sampling, enabling seamless ERP paradigms in children.",
            "metrics": "Disparo de estímulo Go/No-Go sincronizado a nivel de microsegundo.",
            "novelty_claim": "Demuestra la aplicabilidad clínica en neurorrehabilitación lúdica pediátrica.",
            "thesis_ref": "Capítulo 3 (Sección 3.6: Integración con Videojuego Serio), pág. 60",
            "pdf_page": 5,
            "section_ref": "Sección 3 (Materiales y Métodos)",
            "paper_blocks": ["introduction.block-3", "results-and-discussion.rd-contribution-blocks"]
        },

        # =====================================================================
        # 5. ELSEVIER MANUSCRIPT SECTIONS (SAPPHIRE)
        # =====================================================================
        {
            "id": "sec-intro",
            "label": "Sección 1: Inception & Hipótesis",
            "group": "section",
            "color": "#0ea5e9",
            "size": 16,
            "category": "Sección Manuscrito",
            "badge": "PÁGS. 1–3",
            "desc": "Plantea el reto clínico pediátrico en TDAH, la hoja de ruta metodológica de 4 fases y las 3 hipótesis comprobables H1, H2 y H3.",
            "rhetorical_question": "¿Cómo se estructura la justificación clínica y el marco de hipótesis del manuscrito?",
            "paragraph_text": "Pediatric neurodevelopmental disorders, particularly ADHD, place severe demands on clinical assessment and rehabilitation tools... The primary objective of this paper is to demonstrate the empirical and physiological validity of the MONEEG framework under three core hypotheses.",
            "metrics": "Bloques introduction.block-1 al block-6.",
            "novelty_claim": "Fija las preguntas de investigación que gobiernan el manuscrito.",
            "thesis_ref": "Insumo: Introducción y Justificación de la Tesis",
            "pdf_page": 1,
            "section_ref": "Sección 1",
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
            "rhetorical_question": "¿Cómo se posiciona MONEEG frente a las alternativas del estado del arte en canales, ruido y sincronización?",
            "paragraph_text": "Our exploratory 3D atlas compilation of 18 peer-reviewed neurotechnology frameworks confirms that MONEEG occupies a unique quadrant: multi-channel research-grade biopotential precision combined with deterministic stimulus synchronization and pediatric ergonomics, validated under Minciencias-92056 clinical objectives.",
            "metrics": "Tabla tab:sota_comparison, 18 referencias citadas.",
            "novelty_claim": "Posiciona a MONEEG en un cuadrante único de alta densidad + bajo ruido + sincronización determinista.",
            "thesis_ref": "Insumo: Estado del Arte de la Tesis + Atlas 3D",
            "pdf_page": 3,
            "section_ref": "Sección 2",
            "paper_blocks": ["related-work.rw-preamble", "related-work.rw-panorama", "related-work.rw-problem-blocks", "related-work.rw-closing", "related-work.rw-synthesis-artefact"]
        },
        {
            "id": "sec-methods",
            "label": "Sección 3: Materiales & Arquitectura Embebida",
            "group": "section",
            "color": "#0ea5e9",
            "size": 16,
            "category": "Sección Manuscrito",
            "badge": "PÁGS. 4–5",
            "desc": "Describe formalmente el arreglo daisy-chain de 4x ADS1299, el MCU TM4C1294, los rieles de potencia aislados y el casco modular 3D.",
            "rhetorical_question": "¿Cómo se documenta la ingeniería del sistema para garantizar reproducibilidad por otros investigadores?",
            "paragraph_text": "The MONEEG acquisition architecture is structured into four interconnected modules: (1) the 32-channel Analog Front-End (AFE) array; (2) the bare-metal ARM Cortex-M4F embedded acquisition core; (3) the isolated power management and transmission stage; and (4) the ergonomic 3D modular pediatric cap with continuous impedance sensing.",
            "metrics": "Figuras fig:hw_arch, fig:ads_chain, fig:event_sync.",
            "novelty_claim": "Detalla el diseño esquemático y las decisiones de ingeniería para reproducibilidad abierta.",
            "thesis_ref": "Insumo: Capítulo 3 de la Tesis",
            "pdf_page": 4,
            "section_ref": "Sección 3",
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
            "rhetorical_question": "¿Qué montajes y métodos metrológicos se emplearon para auditar objetivamente el hardware?",
            "paragraph_text": "Evaluation metrics included: (i) Input-Referred Noise Floor (Vpp and Vrms across 0.16--70 Hz); (ii) Transmission Stability (Packet Drop Rate over continuous 400-minute streaming); (iii) Event Synchronization Jitter (logic analyzer measurement); and (iv) Physiological Berger Alpha Blocking Ratio.",
            "metrics": "Tasa de muestreo 250 Hz, tramas UDP de 104 bytes.",
            "novelty_claim": "Rigor metodológico exigido por revisores de instrumentación biomédica.",
            "thesis_ref": "Insumo: Capítulo 4 de la Tesis (Protocolos)",
            "pdf_page": 5,
            "section_ref": "Sección 4",
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
            "rhetorical_question": "¿Cuáles son los hallazgos experimentales concretos que corroboran las especificaciones declaradas?",
            "paragraph_text": "Bench testing demonstrated exceptional analog fidelity... In long-term streaming endurance tests, the system operated continuously for 400 minutes, transmitting 1.44 x 10^7 samples with zero dropped packets... In hardware synchronization tests, the measured delay was 2.4 µs with σ = 0.35 µs.",
            "metrics": "Figuras fig:bench_results (ruido/pérdida) y fig:in_vivo_results (latencia/espectrograma).",
            "novelty_claim": "Confirmación empírica indisputable de las tres hipótesis principales.",
            "thesis_ref": "Insumo: Capítulo 4 de la Tesis (Resultados)",
            "pdf_page": 6,
            "section_ref": "Sección 5",
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
            "rhetorical_question": "¿Qué desafíos ingenieriles y clínicos restan por abordar antes del despliegue masivo en clínicas pediátricas?",
            "paragraph_text": "While MONEEG achieves laboratory-grade signal quality and microsecond timing accuracy, several practical considerations must be addressed prior to wide-scale deployment: continuous 32-channel Wi-Fi transmission requires approximately 220 mA, yielding an operating battery life of approximately 4.5 hours.",
            "metrics": "Batería 1200 mAh, blindaje activo en desarrollo.",
            "novelty_claim": "Blindaje editorial contra rechazo de revisores al admitir límites operativos reales.",
            "thesis_ref": "Insumo: Trabajo Futuro de la Tesis",
            "pdf_page": 8,
            "section_ref": "Sección 6",
            "paper_blocks": ["limitations.lim-opening-concession", "limitations.lim-proposal-items", "limitations.lim-validation-items", "limitations.lim-failure-mode", "limitations.lim-closing"]
        },
        {
            "id": "sec-conclusions",
            "label": "Sección 7: Conclusiones & Ciencia Abierta",
            "group": "section",
            "color": "#0ea5e9",
            "size": 15,
            "category": "Sección Manuscrito",
            "badge": "PÁGS. 8–9",
            "desc": "Sintetiza los 4 aportes fundamentales, anuncia la disponibilidad en código abierto de firmware y hardware bajo Minciencias-92056.",
            "rhetorical_question": "¿Cuál es la síntesis de impacto científico y el compromiso de ciencia abierta para la comunidad?",
            "paragraph_text": "This paper introduced MONEEG, an open-source embedded 32-channel electroencephalographic acquisition framework engineered specifically to overcome the timing jitter and ergonomic limitations of contemporary pediatric neurotechnology... establishing an open-source, scalable foundation for accessible neurofeedback in clinical, educational, and ambulatory environments.",
            "metrics": "Bloques concl-1 al concl-4, CRediT formal.",
            "novelty_claim": "Cierre con impacto científico y traslación a neurotecnología accesible.",
            "thesis_ref": "Insumo: Conclusiones de la Tesis",
            "pdf_page": 8,
            "section_ref": "Sección 7",
            "paper_blocks": ["conclusions.concl-block-1", "conclusions.concl-block-2", "conclusions.concl-block-3", "conclusions.concl-block-4"]
        },

        # =====================================================================
        # 6. KEY NOVELTY PARAGRAPH NODES (AMBER / GOLD)
        # =====================================================================
        {
            "id": "p-abstract-solution",
            "label": "Párrafo: Arquitectura y Solución (Abstract)",
            "group": "paragraph",
            "color": "#f59e0b",
            "size": 14,
            "category": "Párrafo de Novedad",
            "badge": "ABSTRACT / PÁG. 1",
            "desc": "Enunciado global de la solución MONEEG en el resumen del manuscrito, declarando los 4 ADS1299 en cascada, el MCU ARM y la inyección en cabecera.",
            "rhetorical_question": "¿Cómo se formula la propuesta integral frente a la comunidad internacional en el Abstract?",
            "paragraph_text": "To address these challenges, this paper presents MONEEG, an open-access embedded 32-channel EEG acquisition framework engineered specifically for pediatric cognitive monitoring and serious game integration. The system integrates four daisy-chained Texas Instruments ADS1299 analog front-ends with a bare-metal ARM Cortex-M4F microcontroller, galvanically isolated power domains, and a custom ergonomic 3D pediatric cap. A hardware-level interrupt mechanism embeds game stimulus trigger flags directly into the 3-byte protocol header at the precise microsecond of analog-to-digital conversion.",
            "metrics": "32 CH, 4x ADS1299, 120 MHz ARM, cabecera 3 bytes.",
            "novelty_claim": "Fija la identidad tecnológica del paper en las primeras 150 palabras del manuscrito.",
            "thesis_ref": "Resumen General y Planteamiento de la Tesis.",
            "pdf_page": 1,
            "section_ref": "Abstract",
            "paper_blocks": ["abstract.slot-3", "abstract.slot-4"]
        },
        {
            "id": "p-intro-gap-jitter",
            "label": "Párrafo: Decomposición de Brecha Temporal (Intro)",
            "group": "paragraph",
            "color": "#f59e0b",
            "size": 13,
            "category": "Párrafo de Novedad",
            "badge": "INTRODUCCIÓN / PÁG. 1",
            "desc": "Párrafo donde se demuestra formalmente cómo el timestamping por software desincroniza los estímulos e invalida el análisis ERP.",
            "rhetorical_question": "¿Por qué los protocolos por software (LSL, UDP) destruyen el alineamiento de potenciales evocados en tareas de alta frecuencia?",
            "paragraph_text": "The survey revealed a persistent technical gap: in available open-source architectures, event markers from interactive stimulation engines (such as serious games) are transmitted via asynchronous software protocols (e.g., LSL, UDP sockets). This introduces stochastic operating system scheduling delays (10--50 ms), completely corrupting the phase alignment necessary for single-trial ERP extraction. Furthermore, analog noise floors often exceed 5 µVpp, washing out low-amplitude microvolt cortical responses.",
            "metrics": "Jitter 10–50 ms en LSL / sockets vs atenuación >40% en P300.",
            "novelty_claim": "Justifica matemáticamente por qué la sincronización por software no es apta para neurofeedback pediátrico de precisión.",
            "thesis_ref": "Capítulo 2 (Marco Teórico y Estado del Arte de la Tesis), pág. 24.",
            "pdf_page": 1,
            "section_ref": "Sección 1 (Introducción)",
            "paper_blocks": ["introduction.block-2"]
        },
        {
            "id": "p-intro-moneeg-mechanism",
            "label": "Párrafo: Mecanismo Co-diseñado MONEEG (Intro)",
            "group": "paragraph",
            "color": "#f59e0b",
            "size": 14,
            "category": "Párrafo de Novedad",
            "badge": "NOVEDAD CENTRAL / PÁG. 2",
            "desc": "Párrafo emblemático de la Introducción (CARS Move 3) donde se devela la arquitectura de co-diseño de hardware de MONEEG.",
            "rhetorical_question": "¿Cómo opera el acople entre el ARM TM4C1294, los 4 ADS1299 y el videojuego Eagle Eye para garantizar sub-5 µs?",
            "paragraph_text": "MONEEG resolves this bottleneck through a co-designed embedded architecture. By combining a bare-metal 120 MHz ARM Cortex-M4F microcontroller (Texas Instruments TM4C1294) with four cascaded ADS1299 analog front-ends (AFEs), the platform performs synchronized 24-bit delta-sigma conversion across 32 channels. Crucially, stimulus event flags generated by the Unity-based serious game Eagle Eye are injected directly into the SPI transfer frame at the hardware interrupt level, guaranteeing sub-5 µs timestamping precision.",
            "metrics": "4 AFEs en cascada, 24 bits, TM4C1294, Eagle Eye en Unity, precisión <5 µs.",
            "novelty_claim": "Define la novedad medular del paper: sincronización en el límite físico de la conversión sin pasar por buffers de SO.",
            "thesis_ref": "Capítulo 3 (Diseño Hardware y Firmware), pág. 48.",
            "pdf_page": 2,
            "section_ref": "Sección 1 (Introducción)",
            "paper_blocks": ["introduction.block-3"]
        },
        {
            "id": "p-intro-hypotheses",
            "label": "Párrafo: Tres Hipótesis Científicas (Intro)",
            "group": "paragraph",
            "color": "#f59e0b",
            "size": 13,
            "category": "Párrafo de Novedad",
            "badge": "HIPÓTESIS H1-H3 / PÁG. 2",
            "desc": "Párrafo donde se enuncian las 3 hipótesis falsables H1 (ruido <1.1 µVpp), H2 (eliminación de jitter) y H3 (casco 3D Z < 10 kΩ).",
            "rhetorical_question": "¿Cuáles son las 3 hipótesis verificables que guían la validación del manuscrito?",
            "paragraph_text": "The primary objective of this paper is to demonstrate the empirical and physiological validity of the MONEEG framework under three core hypotheses: (1) cascaded low-noise front-ends can maintain a sub-microvolt noise floor across 32 active channels under battery power; (2) hardware-embedded event tagging eliminates stimulus-acquisition jitter; and (3) a modular 3D-printed pediatric headpiece maintains stable contact impedance (Z < 10 kΩ) during active gameplay.",
            "metrics": "H1: Vpp < 1.1 µV; H2: Jitter < 5 µs; H3: Z < 10 kΩ.",
            "novelty_claim": "Fija los criterios cuantitativos de éxito que auditará la sección de Resultados.",
            "thesis_ref": "Capítulo 1 (Objetivos e Hipótesis de la Tesis), pág. 12.",
            "pdf_page": 2,
            "section_ref": "Sección 1 (Introducción)",
            "paper_blocks": ["introduction.block-4b"]
        },
        {
            "id": "p-rw-beats-openbci",
            "label": "Párrafo: Benchmark vs. BEATS y OpenBCI (RW)",
            "group": "paragraph",
            "color": "#f59e0b",
            "size": 13,
            "category": "Párrafo de Novedad",
            "badge": "RELATED WORK / PÁGS. 3–4",
            "desc": "Párrafo de discusión comparativa que analiza por qué BEATS sufre preemption de red y por qué OpenBCI carece de sincronización hardware.",
            "rhetorical_question": "¿En qué supera MONEEG a arquitecturas mononúcleo (BEATS) y comerciales (OpenBCI)?",
            "paragraph_text": "Among open-source systems, BEATS represents a notable milestone, delivering 32-channel high-precision acquisition with wireless transmission. However, BEATS utilizes a single-MCU architecture where high-throughput Wi-Fi socket handling can preempt critical time-sensitive ADC servicing under peak network load... Our exploratory 3D atlas compilation of 18 peer-reviewed neurotechnology frameworks confirms that MONEEG occupies a unique quadrant: multi-channel research-grade biopotential precision combined with deterministic stimulus synchronization and pediatric ergonomics.",
            "metrics": "Comparativa contra 18 sistemas (BEATS, OpenBCI, BioSemi, EEGNet).",
            "novelty_claim": "Demuestra la superioridad arquitectónica de separar adquisición estricta y descartar schedulers no deterministas.",
            "thesis_ref": "Capítulo 2 (Taxonomía de Sistemas BCI Existentes), pág. 28.",
            "pdf_page": 3,
            "section_ref": "Sección 2 (Related Work)",
            "paper_blocks": ["related-work.rw-panorama", "related-work.rw-closing"]
        },
        {
            "id": "p-methods-daisychain",
            "label": "Párrafo: Arreglo Daisy-Chain 4x ADS1299 (Methods)",
            "group": "paragraph",
            "color": "#f59e0b",
            "size": 14,
            "category": "Párrafo de Novedad",
            "badge": "MATERIALES / PÁG. 4",
            "desc": "Párrafo técnico que detalla el cascada daisy-chain, el bus SPI común y la captura sincrónica por DMA bajo interrupción DRDY.",
            "rhetorical_question": "¿Cómo se leen 32 canales sincrónicos sin provocar skew temporal ni multiplicar buses de datos?",
            "paragraph_text": "The biopotential acquisition front-end consists of four Texas Instruments ADS1299 integrated circuits connected in a SPI daisy-chain configuration. Each ADS1299 provides eight low-noise, simultaneous-sampling, 24-bit delta-sigma analog-to-digital converters with built-in programmable gain amplifiers (PGA, gain = 1 to 24) and high input impedance (> 1 GΩ). The cascaded SPI configuration allows the host MCU to read all 32 channels (96 bytes plus status words) in a single synchronous DMA transaction triggered by the data-ready (DRDY) hardware interrupt line.",
            "metrics": "4 chips cascada, 96 bytes datos + status, DMA atómico, Zin > 1 GΩ.",
            "novelty_claim": "Asegura sincronismo temporal absoluto entre los 32 canales sin retardos por conmutación de bus.",
            "thesis_ref": "Capítulo 3 (Sección 3.2: Arreglo de Front-Ends Analógicos), Fig. 3.4.",
            "pdf_page": 4,
            "section_ref": "Sección 3 (Materiales y Métodos)",
            "paper_blocks": ["materials-and-methods.mm-borrowed-machinery"]
        },
        {
            "id": "p-methods-isolation",
            "label": "Párrafo: Planos Aislados y Estampado en Cabecera (Methods)",
            "group": "paragraph",
            "color": "#f59e0b",
            "size": 13,
            "category": "Párrafo de Novedad",
            "badge": "MATERIALES / PÁG. 5",
            "desc": "Párrafo que describe el diseño de masa estelar, LDOs ultralimpios TPS7A y la inyección física de marcadores en el encabezado del paquete.",
            "rhetorical_question": "¿Cómo se protegen los microvoltios corticales de las emisiones de radio y cómo se transportan los marcadores de eventos?",
            "paragraph_text": "To decouple noisy digital RF communications from the ultra-sensitive microvolt analog plane, MONEEG features complete galvanic isolation. Separate ground planes are bridged only at a dedicated stellar point, and isolated DC-DC converters deliver clean ±2.5 V analog rails with secondary ultra-low-dropout (LDO) linear regulators (TPS7A49/TPS7A30). The microcontroller embeds stimulus flags directly into the 3-byte protocol header of each transmission packet via an external GPIO interrupt linked to the serious game engine.",
            "metrics": "PSRR > 80 dB, LDOs TPS7A49/TPS7A30, trama UDP de 104 bytes.",
            "novelty_claim": "Estructura de trama de 104 bytes con estampación determinista inmune al ruido electromagnético de la antena Wi-Fi.",
            "thesis_ref": "Capítulo 3 (Sección 3.1: Alimentación y Sección 3.4: Sincronización), págs. 40-56.",
            "pdf_page": 5,
            "section_ref": "Sección 3 (Materiales y Métodos)",
            "paper_blocks": ["materials-and-methods.mm-proposal"]
        },
        {
            "id": "p-results-noise-094",
            "label": "Párrafo: Piso de Ruido 0.94 µVpp Medido (Results)",
            "group": "paragraph",
            "color": "#f59e0b",
            "size": 14,
            "category": "Párrafo de Novedad",
            "badge": "RESULTADOS BANCO / PÁG. 6",
            "desc": "Párrafo clave de resultados empíricos que certifica el piso de ruido submicrovoltio promedio de 0.94 µVpp a lo largo de los 32 canales.",
            "rhetorical_question": "¿Qué niveles de ruido analógico de fondo se alcanzaron en los 32 canales durante los ensayos con entradas en corto?",
            "paragraph_text": "Bench testing demonstrated exceptional analog fidelity. Across all 32 channels, the input-referred noise floor remained strictly under 1.1 µVpp (mean Vpp = 0.94 µV, σ = 0.14 µV, Vrms ≈ 0.16 µV). This is well below the typical amplitude of pediatric scalp EEG (10--100 µV), ensuring that delicate cognitive potentials are preserved without amplifier distortion.",
            "metrics": "Media Vpp = 0.94 µV, σ = 0.14 µV, Vrms ≈ 0.16 µV (0.16–70 Hz).",
            "novelty_claim": "Demuestra que un diseño abierto y de bajo costo puede superar a los amplificadores comerciales de miles de dólares en inmunidad al ruido.",
            "thesis_ref": "Capítulo 4 (Sección 4.1: Caracterización de Ruido de Entrada), Fig. 4.3 de la Tesis.",
            "pdf_page": 6,
            "section_ref": "Sección 5 (Resultados)",
            "paper_blocks": ["results-and-discussion.rd-general-task"]
        },
        {
            "id": "p-results-sync-timing",
            "label": "Párrafo: Latencia 2.4 µs y Cero Pérdidas en 400 Min (Results)",
            "group": "paragraph",
            "color": "#f59e0b",
            "size": 14,
            "category": "Párrafo de Novedad",
            "badge": "RESULTADOS BANCO / PÁG. 6",
            "desc": "Párrafo que reporta los resultados de estrés continuo de 400 minutos y la medición con analizador lógico de la latencia de 2.4 µs.",
            "rhetorical_question": "¿Cómo se comprobó cuantitativamente el fin del jitter temporal y la estabilidad del enlace inalámbrico?",
            "paragraph_text": "In long-term streaming endurance tests, the system operated continuously for 400 minutes, transmitting 1.44 x 10^7 samples with zero dropped packets and bounded inter-sample jitter (< 25 µs). In hardware synchronization tests, the measured delay between the external TTL stimulus trigger and header latching was 2.4 µs with a standard deviation of 0.35 µs, completely outperforming software LSL streaming pipelines (18.5 ± 6.2 ms).",
            "metrics": "400 min continuos, 1.44 x 10^7 muestras, 0 pérdidas, latencia 2.4 µs ± 0.35 µs.",
            "novelty_claim": "Reducción de dispersión temporal de milisegundos a microsegundos (>7,000x más preciso que LSL), posibilitando ERPs de alta precisión.",
            "thesis_ref": "Capítulo 4 (Sección 4.2 y 4.3: Pérdida y Jitter), Figs. 4.6 y 4.9 de la Tesis.",
            "pdf_page": 6,
            "section_ref": "Sección 5 (Resultados)",
            "paper_blocks": ["results-and-discussion.rd-contribution-blocks"]
        },
        {
            "id": "p-results-berger-alpha",
            "label": "Párrafo: Validación Fisiológica Efecto Berger (Results)",
            "group": "paragraph",
            "color": "#f59e0b",
            "size": 14,
            "category": "Párrafo de Novedad",
            "badge": "RESULTADOS IN-VIVO / PÁG. 7",
            "desc": "Párrafo de validación in-vivo con voluntarios humanos donde se comprueba el incremento de 3.8 dB en la banda alfa occipital O2.",
            "rhetorical_question": "¿Cómo se demostró que el sistema captura ritmos cerebrales reales y no artefactos sintéticos?",
            "paragraph_text": "In-vivo physiological validation with healthy volunteers corroborated the system's biological sensitivity. Recording at the occipital electrode O2 during an eyes-open vs. eyes-closed resting state protocol demonstrated clear Berger alpha rhythm attenuation. During the eyes-closed intervals, spectral power in the 8--13 Hz alpha band increased by 3.8 dB relative to eyes-open, providing indisputable proof of physiological ground-truth capture.",
            "metrics": "+3.8 dB en banda alfa (8–13 Hz) en electrodo occipital O2.",
            "novelty_claim": "Prueba empírica de sensibilidad cerebral cortical: modulación alfa natural de 3.8 dB corroborada en espectrograma O2.",
            "thesis_ref": "Capítulo 4 (Sección 4.4: Validación In-Vivo Efecto Berger), Fig. 4.12 de la Tesis.",
            "pdf_page": 7,
            "section_ref": "Sección 5 (Resultados)",
            "paper_blocks": ["results-and-discussion.rd-cost"]
        },
        {
            "id": "p-concl-clinical-takeaway",
            "label": "Párrafo: Impacto Traslacional en TDAH y BCI (Concl)",
            "group": "paragraph",
            "color": "#f59e0b",
            "size": 14,
            "category": "Párrafo de Novedad",
            "badge": "CONCLUSIONES / PÁGS. 8–9",
            "desc": "Párrafo de cierre concluyente que articula el impacto del desacoplamiento de equipos costosos y la democratización del BCI pediátrico.",
            "rhetorical_question": "¿Cuál es el impacto final de democratizar el BCI para niños con TDAH y neurodesarrollo?",
            "paragraph_text": "Beyond the validation of the MONEEG prototype, these findings demonstrate that deterministic hardware-synchronized electroencephalography can be successfully realized in compact, cost-effective embedded form factors without sacrificing clinical microvolt fidelity or pediatric ergonomic feasibility... This decouples pediatric brain-computer interface paradigms from prohibitively expensive, bulky laboratory equipment, establishing an open-source, scalable foundation for accessible neurofeedback and cognitive rehabilitation in clinical, educational, and ambulatory environments.",
            "metrics": "Democratización BCI, desacople de equipos costosos, código y esquemas abiertos.",
            "novelty_claim": "Democratiza la neurorrehabilitación cognitiva infantil: traslada la precisión del laboratorio a la clínica comunitaria y escolar.",
            "thesis_ref": "Capítulo 5 (Conclusiones y Recomendaciones de la Tesis).",
            "pdf_page": 8,
            "section_ref": "Sección 7 (Conclusiones)",
            "paper_blocks": ["conclusions.concl-block-3", "conclusions.concl-block-4"]
        }
    ],

    "links": [
        # --- Core to Gaps ---
        {"source": "core-moneeg", "target": "gap-jitter", "label": "resuelve (sub-5 µs vs 10-50 ms)", "value": 3},
        {"source": "core-moneeg", "target": "gap-noise", "label": "reduce (<1.1 µVpp vs >5 µVpp)", "value": 3},
        {"source": "core-moneeg", "target": "gap-pediatric", "label": "mitiga (casco 3D ergonómico)", "value": 2},
        {"source": "core-moneeg", "target": "gap-preemption", "label": "previene (bare-metal + DMA)", "value": 2},

        # --- Core to Architecture Pillars ---
        {"source": "core-moneeg", "target": "arch-daisychain", "label": "integra (32 CH sincrónicos)", "value": 4},
        {"source": "core-moneeg", "target": "arch-mcu", "label": "ejecuta en (120 MHz determinista)", "value": 3},
        {"source": "core-moneeg", "target": "arch-trigger", "label": "implementa (inyección en cabecera)", "value": 4},
        {"source": "core-moneeg", "target": "arch-power", "label": "protege con (aislamiento galvánico)", "value": 3},
        {"source": "core-moneeg", "target": "arch-cap", "label": "monta en (casco flexible 3D)", "value": 2},

        # --- Architecture Pillars to Thesis Evidence ---
        {"source": "arch-daisychain", "target": "eval-noise", "label": "sustenta piso de ruido", "value": 3},
        {"source": "arch-mcu", "target": "eval-endurance", "label": "garantiza cero desbordes", "value": 3},
        {"source": "arch-trigger", "target": "eval-latency", "label": "demuestra 2.4 µs en banco", "value": 4},
        {"source": "arch-trigger", "target": "eval-game", "label": "sincroniza marcas de Unity", "value": 3},
        {"source": "arch-cap", "target": "eval-berger", "label": "mantiene contacto Z < 10 kΩ", "value": 2},
        {"source": "arch-power", "target": "eval-noise", "label": "elimina rizado de fuente", "value": 2},

        # --- Evidence to Sections ---
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
        {"source": "sec-conclusions", "target": "core-moneeg", "label": "consolida novedad e impacto", "value": 4},

        # --- Key Paragraphs to Sections, Gaps, Pillars, Evidence, Core ---
        {"source": "p-abstract-solution", "target": "core-moneeg", "label": "declara formalmente", "value": 4},
        {"source": "p-abstract-solution", "target": "sec-intro", "label": "resume alcance de", "value": 3},
        
        {"source": "p-intro-gap-jitter", "target": "sec-intro", "label": "párrafo de apertura de", "value": 3},
        {"source": "p-intro-gap-jitter", "target": "gap-jitter", "label": "formula cuantitativamente", "value": 4},
        
        {"source": "p-intro-moneeg-mechanism", "target": "sec-intro", "label": "párrafo central de", "value": 4},
        {"source": "p-intro-moneeg-mechanism", "target": "core-moneeg", "label": "enuncia innovación de", "value": 4},
        {"source": "p-intro-moneeg-mechanism", "target": "arch-trigger", "label": "presenta mecanismo de", "value": 4},
        {"source": "p-intro-moneeg-mechanism", "target": "arch-mcu", "label": "establece bare-metal en", "value": 3},

        {"source": "p-intro-hypotheses", "target": "sec-intro", "label": "cierre propositivo de", "value": 3},
        {"source": "p-intro-hypotheses", "target": "eval-noise", "label": "fija hipótesis H1", "value": 3},
        {"source": "p-intro-hypotheses", "target": "eval-latency", "label": "fija hipótesis H2", "value": 3},
        {"source": "p-intro-hypotheses", "target": "arch-cap", "label": "fija hipótesis H3", "value": 3},

        {"source": "p-rw-beats-openbci", "target": "sec-rw", "label": "párrafo de contraste en", "value": 3},
        {"source": "p-rw-beats-openbci", "target": "gap-preemption", "label": "demuestra vulnerabilidad de", "value": 3},
        {"source": "p-rw-beats-openbci", "target": "core-moneeg", "label": "ubica en cuadrante único a", "value": 3},

        {"source": "p-methods-daisychain", "target": "sec-methods", "label": "párrafo de diseño en", "value": 3},
        {"source": "p-methods-daisychain", "target": "arch-daisychain", "label": "formaliza ingeniería de", "value": 4},
        {"source": "p-methods-daisychain", "target": "eval-noise", "label": "habilita piso de ruido de", "value": 3},

        {"source": "p-methods-isolation", "target": "sec-methods", "label": "párrafo de aislamiento en", "value": 3},
        {"source": "p-methods-isolation", "target": "arch-power", "label": "especifica LDOs y masas de", "value": 3},
        {"source": "p-methods-isolation", "target": "arch-trigger", "label": "define trama 104B de", "value": 3},

        {"source": "p-results-noise-094", "target": "sec-results", "label": "párrafo de validación en", "value": 4},
        {"source": "p-results-noise-094", "target": "eval-noise", "label": "reporta 0.94 µVpp medido en", "value": 4},
        {"source": "p-results-noise-094", "target": "gap-noise", "label": "derrota brecha de", "value": 4},

        {"source": "p-results-sync-timing", "target": "sec-results", "label": "párrafo de latencia en", "value": 4},
        {"source": "p-results-sync-timing", "target": "eval-latency", "label": "reporta 2.4 µs ± 0.35 µs de", "value": 4},
        {"source": "p-results-sync-timing", "target": "eval-endurance", "label": "certifica 400 min de", "value": 3},
        {"source": "p-results-sync-timing", "target": "gap-jitter", "label": "elimina definitivamente", "value": 4},

        {"source": "p-results-berger-invivo", "target": "sec-results", "label": "párrafo in-vivo en", "value": 4},
        {"source": "p-results-berger-invivo", "target": "eval-berger", "label": "presenta modulación 3.8 dB de", "value": 4},

        {"source": "p-concl-clinical-takeaway", "target": "sec-conclusions", "label": "párrafo de remate en", "value": 4},
        {"source": "p-concl-clinical-takeaway", "target": "core-moneeg", "label": "proyecta legado y futuro de", "value": 4},
        {"source": "p-concl-clinical-takeaway", "target": "gap-pediatric", "label": "resuelve traslación en", "value": 3}
    ]
}


def build_novelty_graph() -> dict[str, Any]:
    """Return the complete semantic novelty graph for MONEEG."""
    return NOVELTY_GRAPH_DATA


def build_novelty_viewer_html() -> str:
    """Generate the full responsive 3D WebGL viewer for the novelty graph,
    matching the exact style, typography, libraries, and constellation aesthetics of SOTA Atlas."""
    graph_json = json.dumps(NOVELTY_GRAPH_DATA, ensure_ascii=False)
    
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Grafo 3D de Novedad e Ideas del Manuscrito — MONEEG</title>
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
      gap: 5px;
    }}
    #toolbar button {{
      font-size: 12px;
      padding: 3px 10px;
      cursor: pointer;
      background: #14172a;
      color: #e4e4ed;
      border: 1px solid #2a3350;
      border-radius: 6px;
      transition: background 0.15s, border-color 0.15s;
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
      width: 210px;
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
      border-left: 3px solid #f59e0b;
      margin: 10px 0;
      padding: 8px 12px;
      background: rgba(245, 158, 11, 0.05);
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
    <span>🕸️ Grafo 3D de Novedad e Ideas del Manuscrito — MONEEG</span>
    <small>Elsevier Biomedical Signal Processing and Control · Minciencias-92056</small>
  </h1>
  <div id="panel">Arrastra para rotar, clic derecho para desplazar, rueda para zoom. Pasa el cursor sobre un nodo para trazar enlaces y atenuar el resto; clic para ver detalles y evidencia; clic en los chips para agrupar por color las partes del manuscrito.</div>

  <!-- Legend & Color Grouping Chips (Atlas Style) -->
  <div id="famlegend"><em>Agrupar por Color:</em> <span id="famchips"></span></div>
  <div id="rellegend"><em>Enlaces:</em> <span class="dot" style="border-color:#38bdf8"></span>arquitectura <span class="dot" style="border-color:#f59e0b"></span>párrafo clave <span class="dot" style="border-color:#f43f5e"></span>resuelve brecha <span class="dot" style="border-color:#10b981"></span>hardware determinista <span class="dot" style="border-color:#a855f7"></span>evidencia tesis</div>

  <!-- Toolbar Controls (Atlas Style) -->
  <div id="toolbar">
    <button id="zoomin">zoom +</button>
    <button id="zoomout">zoom −</button>
    <button id="zoomreset">reset view</button>
    <button id="btnAutoRotate">pausar giro</button>
    <input type="text" id="nodeSearchInput" placeholder="🔍 Buscar nodo, párrafo o métrica..." oninput="searchNodes(this.value)">
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

    const highlightNodes = new Set();
    const highlightLinks = new Set();

    const elem = document.getElementById('3d-graph');
    const Graph = ForceGraph3D()(elem)
      .graphData(graphData)
      .backgroundColor('#0a0a10')
      .showNavInfo(false)
      .nodeLabel(node => `${{node.label}} [${{node.category}}]`)
      .nodeVal(node => node.size || 10)
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
        if (link.source && (link.source.group === 'paragraph' || link.source === 'paragraph')) return 'rgba(245, 158, 11, 0.45)';
        return 'rgba(56, 189, 248, 0.35)';
      }})
      .linkDirectionalParticles(2)
      .linkDirectionalParticleWidth(link => {{
        if (highlightLinks.size > 0 && !highlightLinks.has(link)) return 0;
        return 1.8;
      }})
      .linkDirectionalParticleSpeed(0.005)
      .linkDirectionalParticleColor(link => {{
        if (link.source && (link.source.group === 'paragraph' || link.source === 'paragraph')) return '#f59e0b';
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
          if (n.group === activeGroup || (activeGroup === 'paragraph' && (n.group === 'paragraph' || n.group === 'section' || n.id === 'core-moneeg'))) {{
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

    // Auto-orbit camera
    let angle = 0;
    const distance = 480;
    setInterval(() => {{
      if (isRotating) {{
        angle += 0.0022;
        Graph.cameraPosition({{
          x: distance * Math.sin(angle),
          z: distance * Math.cos(angle)
        }});
      }}
    }}, 20);

    function toggleRotate() {{
      isRotating = !isRotating;
      const btn = document.getElementById('btnAutoRotate');
      btn.textContent = isRotating ? 'pausar giro' : 'reanudar giro';
      btn.classList.toggle('active', !isRotating);
    }}
    document.getElementById('btnAutoRotate').addEventListener('click', toggleRotate);

    document.getElementById('zoomin').addEventListener('click', () => {{
      const pos = Graph.cameraPosition();
      Graph.cameraPosition({{ x: pos.x * 0.75, y: pos.y * 0.75, z: pos.z * 0.75 }}, null, 400);
    }});

    document.getElementById('zoomout').addEventListener('click', () => {{
      const pos = Graph.cameraPosition();
      Graph.cameraPosition({{ x: pos.x * 1.33, y: pos.y * 1.33, z: pos.z * 1.33 }}, null, 400);
    }});

    document.getElementById('zoomreset').addEventListener('click', () => {{
      isRotating = false;
      document.getElementById('btnAutoRotate').textContent = 'reanudar giro';
      document.getElementById('btnAutoRotate').classList.add('active');
      activeGroup = null;
      document.querySelectorAll('.famchip').forEach(c => {{
        c.classList.remove('on');
        c.style.background = '#14172a';
        c.style.color = '#e4e4ed';
      }});
      updateHighlight();
      Graph.nodeColor(Graph.nodeColor()).linkColor(Graph.linkColor()).linkWidth(Graph.linkWidth());
      Graph.cameraPosition({{ x: 0, y: 35, z: 460 }}, {{ x: 0, y: 0, z: 0 }}, 1000);
    }});

    function selectNode(node) {{
      selectedNode = node;
      isRotating = false;
      document.getElementById('btnAutoRotate').textContent = 'reanudar giro';
      document.getElementById('btnAutoRotate').classList.add('active');

      const dist = 180;
      Graph.cameraPosition(
        {{ x: node.x + dist * 0.7, y: node.y + dist * 0.35, z: node.z + dist * 0.7 }},
        {{ x: node.x, y: node.y, z: node.z }},
        1000
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
      document.getElementById('inspLocation').textContent = `${{node.section_ref || 'Manuscrito'}} · Ubicación en documento final: Página ${{targetPdfPage}}`;

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

    // Build Family Legend Chips (Atlas Style)
    const GROUPS_META = [
      {{ id: 'core', label: 'Novedad Central & Abstract', color: '#38bdf8' }},
      {{ id: 'paragraph', label: 'Párrafos Clave de Novedad', color: '#f59e0b' }},
      {{ id: 'gap', label: 'Brechas Clínicas y SOTA', color: '#f43f5e' }},
      {{ id: 'arch', label: 'Arquitectura Hardware', color: '#10b981' }},
      {{ id: 'eval', label: 'Evidencia Experimental Tesis', color: '#a855f7' }},
      {{ id: 'section', label: 'Secciones del Manuscrito', color: '#0ea5e9' }}
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
