---
{
  "section": "results-and-discussion",
  "position": 7,
  "mode": {
    "value": "argument",
    "source": {
      "file": "sections/03-results-and-discussion.md",
      "quote": "La discusión es inferencial por defecto y asertiva por excepción."
    }
  },
  "blocks": [
    {
      "id": "rd-general-task",
      "requires_facts": [
        {
          "value": "results",
          "source": {
            "file": "sections/03-results-and-discussion.md",
            "quote": "Los resultados — las ejecuciones principales, contra las líneas base"
          }
        }
      ],
      "requires_declarations": [],
      "citations": "resolution"
    },
    {
      "id": "rd-contribution-blocks",
      "requires_facts": [
        {
          "value": "contributions",
          "source": {
            "file": "sections/03-results-and-discussion.md",
            "quote": "La propiedad que una contribución prometió, y el instrumento que la configuración nombró para ella"
          }
        },
        {
          "value": "results",
          "source": {
            "file": "sections/03-results-and-discussion.md",
            "quote": "Entrada los resultados de los experimentos"
          }
        }
      ],
      "requires_declarations": [],
      "citations": "resolution",
      "after": [
        {
          "target": "results-and-discussion.rd-general-task",
          "source": {
            "file": "sections/03-results-and-discussion.md",
            "quote": "Un bloque de mecanismo abre nombrando el resultado del bloque anterior como la pregunta que viene a responder."
          }
        },
        {
          "target": "materials-and-methods.mm-proposal",
          "source": {
            "file": "sections/03-results-and-discussion.md",
            "quote": "La propiedad que una contribución prometió, y el instrumento que la configuración nombró para ella"
          }
        }
      ]
    },
    {
      "id": "rd-cost",
      "requires_facts": [
        {
          "value": "results",
          "source": {
            "file": "sections/03-results-and-discussion.md",
            "quote": "Entrada los resultados de los experimentos"
          }
        },
        {
          "value": "implementation",
          "source": {
            "file": "sections/03-results-and-discussion.md",
            "quote": "La implementación — la configuración más exigente, y el hardware declarado en la configuración experimental"
          }
        }
      ],
      "requires_declarations": [],
      "citations": "none",
      "optional": true,
      "after": [
        {
          "target": "results-and-discussion.rd-contribution-blocks",
          "source": {
            "file": "sections/03-results-and-discussion.md",
            "quote": "Un bloque de mecanismo abre nombrando el resultado del bloque anterior como la pregunta que viene a responder."
          }
        }
      ]
    }
  ]
}
---
# Resultados y Discusión

**Extensión** 1170–4150 palabras · dos o tres bloques de contenido, más las limitaciones al final
**Entrada** los resultados de los experimentos
**Contiene** 5–14 figuras y 0–4 tablas — la sección del artículo con mayor densidad de artefactos
**No contiene** un preámbulo, un artefacto de cierre ni una sola ecuación numerada

## Una sección, nunca dos

La discusión no es un bloque. No hay un tramo separado de prosa de discusión: la
discusión es **el tercer tiempo de cada lectura de artefacto, en el mismo párrafo que
el número que explica**. Por eso ambas son una sola sección y por eso no pueden
separarse.

## Los bloques

**1. La tarea general.** La evidencia de que la propuesta funciona en la tarea para la que fue
construida: la métrica principal, sobre los datos principales, contra las líneas base. Este bloque
contiene el grueso de la sección — entre el 40% y el 66% de ella.

**2. Un bloque por contribución.** Cada uno valida la propiedad que esa contribución
prometió, usando el instrumento que la configuración experimental nombró para ella.

**3. Costo, cuando se afirma el costo.** Uno o dos párrafos, una figura. Medido en la
configuración más exigente, y enunciado como tal para que la estimación se lea como
conservadora.

**4. Limitaciones.** Al final, siempre, bajo su propio contrato.

### Organizar por escenario en su lugar

Cuando el trabajo tiene escenarios experimentales disímiles — dominios distintos, regímenes
de datos distintos — los bloques pueden organizarse uno por escenario, cada uno recorriendo
internamente desempeño-y-luego-mecanismo. **La correspondencia con las contribuciones se
sigue enunciando**, para que el lector sepa qué bloque valida qué contribución.
Organizar por escenario sin decirlo es lo que hace perder la correspondencia.

## La cadena que termina aquí

> **problema *i* → contribución *i* → propiedad *i* → instrumento *i* → evidencia *i***

El problema se declaró en el planteamiento del problema, la brecha dijo que nadie lo había resuelto,
la contribución lo responde, la configuración nombró el instrumento que lo mide, y
esta sección es donde aparece la evidencia. **La propiedad lleva el mismo nombre
a través de los cinco eslabones** — no un sinónimo, las mismas palabras.

La obligación va en ambos sentidos:

- **cada contribución tiene un bloque aquí**, y
- **cada bloque aquí pertenece a una contribución o a la tarea general.**

Un bloque que no pertenece a ninguna es una medición que nadie pidió.

## Cómo se presenta un resultado

La forma es la misma para una figura y para una tabla. Dos posiciones sintácticas:

**El artefacto como sujeto gramatical**, seguido de un verbo de lectura y de lo que
muestra.

**El artefacto como referencia dentro de la afirmación** — la forma usada siempre que hay un
valor:

> **[la afirmación en palabras] + [el valor entre paréntesis] + [la referencia al artefacto]**

**La referencia apunta al subelemento exacto, no al artefacto en su conjunto.**
Cuando un artefacto tiene partes — paneles, columnas, bandas de filas, lados, regiones sombreadas — la
referencia nombra la parte. Enviar al lector a un artefacto completo para encontrar un número es
enviarlo a buscarlo.

**Los verbos de lectura son un conjunto cerrado con un gradiente.** Los neutros dicen que el artefacto
exhibe algo: *presenta, muestra, ilustra, representa, proporciona*. Los asertivos
dicen que establece algo: *revela, demuestra, confirma, identifica*. Use la
forma asertiva solo cuando el artefacto zanja la cuestión.

## Cada artefacto se referencia antes de aparecer

Cualquier objeto numerado — figura, tabla o panel — se referencia en el cuerpo **antes**
de aparecer. Sin excepción.

El valor diagnóstico es lo esencial: **un artefacto que aparece sin referencia previa
está mal ubicado o está muerto.** Aplicar esta regla es la forma de encontrar una figura a la que nada en el
artículo hace referencia.

## El movimiento de tres tiempos

Por artefacto: **señalarlo → leerlo en números → dar el mecanismo.** Los tres, en
ese orden, en el mismo párrafo. El tercer tiempo es lo que separa reportar de
explicar.

**Un número en la prosa viene con su referencia.** La prosa nunca introduce un valor que ningún
artefacto muestre.

## La discusión: tres registros

El tercer tiempo se presenta en tres registros, y no son intercambiables.

| Registro | Proporción | Forma | Cuándo |
|---|---|---|---|
| **Inferencial** | ~57% | *indica, sugiere, es consistente con, refleja* | el mecanismo se infiere del patrón |
| **Asertivo** | ~30% | *porque, debido a, se deriva de, se atribuye a* | el mecanismo es una propiedad conocida de la formulación o de los datos, no una inferencia a partir del resultado |
| **Corroborativo** | ~13% | *confirma, refuerza* | el resultado concuerda con un bloque anterior o con un comportamiento establecido |

**La discusión es inferencial por defecto y asertiva por excepción.** Dos de cada
tres explicaciones dicen con qué es *consistente* el número, no qué lo *causó*. Una
discusión escrita enteramente en el registro asertivo afirma un conocimiento causal
que el experimento no produjo.

**Está anclada.** La explicación se ubica en el mismo párrafo que el número que
explica. Nunca queda flotando.

**Se encadena entre bloques.** Un bloque de mecanismo abre nombrando el resultado del bloque anterior como la pregunta que viene a responder.

**La concesión pertenece a la discusión.** Donde un competidor gana un subcriterio,
dígalo, y diga qué compra esa pérdida.

**Tres cosas que la discusión no hace:** introducir una afirmación que ningún artefacto respalda;
reformular el número en palabras sin agregar un mecanismo; o saltar a implicaciones para
la práctica — eso pertenece a las conclusiones.

## Cuando una contribución no tiene competidor

Algunas contribuciones no tienen nada contra qué compararse, porque nada más hace
eso. Tres movimientos, en orden:

1. **Proyectar hacia un espacio compartido donde la comparación sea posible**, y mostrar
   **paridad** allí — paridad, no superioridad. Si la contribución opera sobre más
   dimensiones que cualquier competidor, redúzcala a la dimensión que comparten y muestre que
   se sostiene.
2. **Mostrar lo que solo esta contribución produce** — la parte en la que ningún competidor puede ser
   medido. No hay comparación allí porque no hay nada con qué comparar,
   y esa ausencia es el argumento.
3. **Si la paridad es en realidad una pérdida, concederla y enunciar qué se compra con ella.**

**La salvaguarda:** una pérdida concedida se empareja con una ganancia **medida**, no con una
afirmada. Ambas apuntan a un artefacto. *Perdemos aquí pero somos mejores allá* se sostiene solo si
*allá* tiene su propia celda reportada. Sin esta salvaguarda, cualquier resultado desfavorable puede
reciclarse como una virtud.

**Y la deficiencia aun así va a las limitaciones como un ítem.** Justificada aquí se lee
defensiva; declarada allá se lee honesta, y solo allá puede ganarse una dirección de
trabajo futuro.

## El tipo de artefacto sigue a la afirmación

Una cuadrícula de números es una tabla. Un patrón espacial, temporal o espectral es una figura.
Esta no es una preferencia de estilo: un bloque cuya afirmación es una comparación entre celdas
lleva tablas y puede no llevar ninguna figura, mientras que un bloque cuya afirmación es un patrón
lleva figuras y puede no llevar ninguna tabla.

## Citas

Casi ninguna — y nunca para un resultado. Una cita aquí acredita **un instrumento** usado
para leer los datos, o un **comportamiento ya establecido** con el que el resultado concuerda.

## Entradas

### Entradas externas

| Entrada | Desbloquea |
|---|---|
| Los **resultados** — las ejecuciones principales, contra las líneas base | `rd-general-task` |
| La **implementación** — la configuración más exigente, y el hardware declarado en la configuración experimental | `rd-cost` |

### Cadena interna

| Bloque | Depende de |
|---|---|
| `results-and-discussion.rd-contribution-blocks` — un bloque de mecanismo abre nombrando el resultado del bloque anterior como la pregunta que viene a responder | `results-and-discussion.rd-general-task` — la evidencia de la tarea general, el bloque inmediatamente anterior |
| `results-and-discussion.rd-contribution-blocks` — La propiedad que una contribución prometió, y el instrumento que la configuración nombró para ella | `materials-and-methods.mm-proposal` — las contribuciones enumeradas a las que se rastrea cada propiedad |
| `results-and-discussion.rd-cost` — un bloque de mecanismo abre nombrando el resultado del bloque anterior como la pregunta que viene a responder | `results-and-discussion.rd-contribution-blocks` — la validación por contribución, el bloque inmediatamente anterior al costo |

### Decisiones estructurales

- **Cada artefacto** depende de las ejecuciones, y el diagrama de cierre de la configuración
  experimental debe poder ubicarlo — una regla transversal a todos los bloques de aquí,
  no una dependencia de un bloque específico.
- **El tercer tiempo** (la explicación mecanística) se apoya en la formulación,
  o en una propiedad de los datos — de nuevo transversal a todos los bloques, sin
  nombrar uno.
- **Limitaciones** vive en su propia sección, bajo su propio contrato — no es
  un bloque de esta sección y no tiene ninguna dependencia de ella.

## Descalificadores

- Una ecuación numerada.
- Un preámbulo, o un artefacto de resumen de cierre.
- Un bloque que abre con prosa sin referencia a un artefacto.
- Un artefacto que aparece antes de cualquier referencia a él, o al que nada referencia en
  absoluto.
- Una referencia a un artefacto completo cuando el valor está en una de sus partes.
- Un número en la prosa que no aparece en ningún artefacto.
- Un artefacto que no puede ubicarse en el diagrama de cierre de la configuración experimental —
  una celda reportada que el diseño nunca declaró.
- Una afirmación de mejora sin la línea base sobre la que mejora, en el mismo artefacto.
- Una contribución sin un bloque aquí.
- Un bloque que no pertenece ni a una contribución ni a la tarea general.
- Una propiedad nombrada aquí con un nombre distinto al que le dieron el planteamiento del problema, la
  contribución o el instrumento.
- Un bloque organizado por escenario sin enunciar qué contribución valida.
- Una lectura de artefacto sin tercer tiempo — el número enunciado y nunca explicado.
- Una discusión escrita enteramente en el registro asertivo.
- Una explicación ubicada en un párrafo distinto del número que explica.
- Una pérdida concedida emparejada con una ganancia afirmada en lugar de una medida.
- Una deficiencia justificada aquí y ausente de las limitaciones.
- Una cita acreditada a un resultado.
- Una tabla usada para un patrón, o una figura usada para una cuadrícula de comparación.
- Las limitaciones ubicadas en cualquier lugar que no sea el final.
- La interpretación de un resultado que ningún artefacto contiene.
