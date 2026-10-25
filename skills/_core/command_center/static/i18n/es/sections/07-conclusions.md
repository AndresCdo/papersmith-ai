---
{
  "section": "conclusions",
  "position": 9,
  "mode": {
    "value": "transposition",
    "source": {
      "file": "sections/07-conclusions.md",
      "quote": "No añaden nada — toda afirmación aquí ya existe antes, con más detalle."
    }
  },
  "blocks": [
    {
      "id": "concl-block-1",
      "requires_facts": [
        {
          "value": "contributions",
          "source": {
            "file": "sections/07-conclusions.md",
            "quote": "Las contribuciones, tal como se definieron — mismo número, orden y nombres que en la introducción y en la sección de métodos"
          }
        }
      ],
      "requires_declarations": [],
      "citations": "none",
      "after": [
        {
          "target": "materials-and-methods.mm-proposal",
          "source": {
            "file": "sections/07-conclusions.md",
            "quote": "Las contribuciones, tal como se definieron — mismo número, orden y nombres que en la introducción y en la sección de métodos"
          }
        }
      ]
    },
    {
      "id": "concl-block-2",
      "requires_facts": [
        {
          "value": "results",
          "source": {
            "file": "sections/07-conclusions.md",
            "quote": "Los resultados, y el número de escenarios experimentales, que decide si es un párrafo o dos"
          }
        }
      ],
      "requires_declarations": [],
      "citations": "none"
    },
    {
      "id": "concl-block-3",
      "requires_facts": [],
      "requires_declarations": [],
      "citations": "none"
    },
    {
      "id": "concl-block-4",
      "requires_facts": [
        {
          "value": "limitations",
          "source": {
            "file": "sections/07-conclusions.md",
            "quote": "Las limitaciones, de las que es el subconjunto pertinente, y una referencia por dirección"
          }
        }
      ],
      "requires_declarations": [],
      "citations": "resolution",
      "after": [
        {
          "target": "limitations.lim-proposal-items",
          "source": {
            "file": "sections/07-conclusions.md",
            "quote": "Las limitaciones, de las que es el subconjunto pertinente, y una referencia por dirección"
          }
        }
      ]
    }
  ]
}
---
# Conclusiones

**Extensión** 375–500 palabras · 3 o 4 párrafos
**No contiene** ecuaciones, figuras ni tablas
**Contiene** citas en un solo lugar: el bloque de trabajo futuro

Las conclusiones las leen personas que no leerán el artículo. Deben sostenerse
por sí solas. No añaden nada — toda afirmación aquí ya existe antes, con más detalle.

## Cuatro bloques funcionales

| Bloque | Párrafos | Palabras |
|---|---|---|
| 1 — La propuesta y sus componentes | 1, siempre el primero | 60–226 |
| 2 — La recapitulación de resultados | 1 o 2 | 100–180 cada uno |
| 3 — La consecuencia más allá del método | párrafo propio, o el cierre del bloque 2 | ~50–120 |
| 4 — Trabajo futuro | 1, siempre el último | 55–180 |

Los bloques 2 y 3 pueden compartir un párrafo; los bloques 1 y 4 nunca se fusionan con nada.

## Bloque 1 — La propuesta y sus componentes

Tiempo pasado. Nombre completo, sigla y la categoría del artefacto. Luego los N
componentes reformulados, en una de tres formas:

- **`First / Second / Third`** como oraciones separadas, tras anunciar el número;
- **una lista en línea** dentro de una sola oración, la forma más compacta;
- **prosa con conectores**: *integrando A … la incorporación de B permite … 
  además C*.

**Mismo número, mismo orden, mismos nombres** que la lista de contribuciones de la introducción y
las subsecciones de la sección de métodos.

**Cerrar con lo que distingue al método de sus alternativas**: la propiedad, no
el número. Lo que no requiere, lo que no necesita modificar, aquello de lo que no
depende.

## Bloque 2 — La recapitulación de resultados

Competidores con nombre, ejes con nombre y el hallazgo específico con las condiciones bajo las
cuales se cumplió.

**Uno o dos párrafos, y el número de escenarios experimentales lo decide.** Dos
escenarios disímiles llevan un párrafo cada uno. Un único escenario aún puede dividirse en
resultado y mecanismo: cuáles fueron los números y con qué era consistente el
patrón.

**Se permiten cifras, con dispersión, pero no son la norma.** Cite un valor
solo cuando el valor es lo importante; de lo contrario, manténgase en comparativos. Una cifra citada
debe coincidir exactamente con la sección de resultados.

## Bloque 3 — La consecuencia más allá del método

Lo que el lector se lleva, más allá del hecho de que el método funcionó. No es un resultado ni
una contribución: es una consecuencia. Responde a *y qué*.

Dos variantes; el artículo elige según de quién sea el problema:

- **Para quien lo implementa**: el costo de adopción es bajo: no hay que
  modificar nada, la arquitectura se integra en los flujos existentes, el tiempo de predicción disminuye.
- **Para quien vive el problema**: algo se vuelve posible que antes no lo era: el
  factor detrás de una predicción puede rastrearse, la ruta de decisión es auditable donde
  la regulación lo exige.

Puede ser su propio párrafo o las oraciones de cierre del bloque 2. Es la única parte
de la sección que se dirige a alguien fuera del subcampo.

## Bloque 4 — Trabajo futuro

Siempre al final. **El único bloque de la sección que cita**: una referencia por
dirección, que muestra que la dirección está viva en la literatura. Todo lo anterior
no cita nada.

**El trabajo futuro es el subconjunto pertinente de las limitaciones, con una referencia por
dirección.** Cada dirección responde a una limitación declarada.

**La reducción va en un solo sentido.** Una limitación puede quedar sin dirección:
no todo está pensado para repararse. Pero ninguna dirección queda sin una limitación
que la motive: **una dirección sin limitación correspondiente significa que la limitación
nunca se declaró**, no que la dirección sea innecesaria. Se corrige declarando la
limitación, no eliminando la dirección.

Eso es lo que hace verificable el acoplamiento entre las dos secciones.

Cada dirección es lo bastante específica como para ser un artículo: una extensión con nombre, no una esperanza.
El bloque cierra con la aplicabilidad que esas direcciones ampliarían.

## Opcional

**Una advertencia de alcance.** Cuando los resultados podrían leerse como un hallazgo sobre el dominio
y no sobre el modelo, diga cuál de los dos son. Esto conlleva la misma
disciplina de atribución que una cifra citada: indicar a qué pertenece la afirmación.

## Estilo de la casa LIA

Medido sobre los diez artículos de método Q1 del grupo de 2025–2026 (SJR 2025): ítems A003, A006, A007, A009, A012, A013, A021, A022, A023 y A026 del banco de artículos del laboratorio. Los rangos son mínimo–mediana–máximo entre los artículos que tienen la sección; una línea compuesta tiene unas 12 palabras en un formato de una columna. Los rangos describen cómo escribe el grupo; la extensión indicada al inicio de este contrato sigue siendo la meta.

**Tamaño medido.** 2–4–10 párrafos; 252–482–950 palabras, unas 22–43–85 líneas;
95–127–158 palabras por párrafo; sin ecuaciones, figuras ni tablas; 0–3–4 citas, en
las oraciones de trabajo futuro.

**Forma.** Titulada *Conclusions*, o *Concluding Remarks and Future Work*. Abre
reformulando el método en pasado (*This work introduced …, a …*), repite las cifras
clave y cierra con el trabajo futuro enumerado como *First*, *Second*, *Third*.

**Redacción.**

- **Las oraciones promedian 21–27 palabras.** Lo bastante largas para portar una afirmación y su matiz, nunca una cadena de tres cláusulas.
- **Una sola voz para todo el artículo.** Primera persona del plural (*we propose*) o impersonal (*this work introduces*), elegida una sola vez; los procedimientos que se ejecutaron van en voz pasiva y en pasado (*was evaluated using*).
- **Conectores que usa el grupo** para pasar de una afirmación a otra: *However*, *Specifically*, *In particular*, *Moreover*, *Notably*, *Overall*. Cada uno abre una oración y cumple una sola función: contraste, acotación, adición, énfasis, síntesis.
- **El método tiene un solo nombre.** Se desarrolla junto con su acrónimo en su primera aparición, tanto en el resumen como en el cuerpo, y en adelante se usa *the proposed* seguido del acrónimo.

## Entradas

Todo excepto el resumen debe existir. El resumen se escribe después de esta
sección, porque la comprime.

### Entradas externas

| Entrada | Desbloquea |
|---|---|
| Los **resultados**, y el número de escenarios experimentales, que decide si es un párrafo o dos | `concl-block-2` |

### Cadena interna

| Bloque | Depende de |
|---|---|
| `conclusions.concl-block-1` — Las contribuciones, tal como se definieron — mismo número, orden y nombres que en la introducción y en la sección de métodos | `materials-and-methods.mm-proposal` — las contribuciones enumeradas que aquí se reformulan |
| `conclusions.concl-block-4` — Las limitaciones, de las que es el subconjunto pertinente, y una referencia por dirección | `limitations.lim-proposal-items` — las limitaciones recopiladas de las que este bloque extrae su subconjunto pertinente |

La ubicación propia del bloque 3 (su propio párrafo o el cierre del bloque 2) es una
opción de ubicación (véase Decisiones estructurales), no una derivación de contenido a partir de
la propia prosa del bloque 2, por lo que `concl-block-3` no lleva ni una entrada externa ni
una fila de cadena interna.

### Decisiones estructurales

- **Bloque 3 — la consecuencia más allá del método** se elige según de quién sea
  el problema: del implementador o del dominio; es una decisión autoral, no un
  hecho obtenido de los datos ni una dependencia de un bloque hermano.

## Descalificadores

- Una afirmación, un número o una propiedad que no aparece en ninguna parte anterior del artículo.
- Una lista de componentes que discrepa de la introducción o de la sección de métodos en número,
  orden o nombres.
- El bloque 1 que no va primero, o el bloque 4 que no va al final.
- El bloque 1 que cierra con un número en lugar de con la propiedad distintiva.
- Una cifra citada que no coincide exactamente con la sección de resultados.
- Una dirección de trabajo futuro que no responde a ninguna limitación declarada.
- Una cita en cualquier lugar fuera del bloque de trabajo futuro.
- Una dirección de trabajo futuro sin referencia.
- Una dirección de trabajo futuro demasiado vaga para ser un artículo.
- Una ecuación, una figura o una tabla.
- Limitaciones desarrolladas aquí en lugar de en la sección de resultados.
- Más de 500 o menos de 375 palabras.
- Una sección que no puede leerse sin haber leído el artículo.
