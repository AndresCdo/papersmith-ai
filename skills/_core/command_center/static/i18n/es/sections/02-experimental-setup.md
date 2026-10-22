---
{
  "section": "experimental-setup",
  "position": 6,
  "mode": {
    "value": "transposition",
    "source": {
      "file": "sections/02-experimental-setup.md",
      "quote": "Nada aquí se descubre: cada condición que esta sección enuncia ya estaba fijada cuando se ejecutaron los experimentos."
    }
  },
  "blocks": [
    {
      "id": "es-preamble",
      "requires_facts": [],
      "requires_declarations": [],
      "citations": "none"
    },
    {
      "id": "es-dataset",
      "requires_facts": [
        {
          "value": "dataset",
          "source": {
            "file": "sections/02-experimental-setup.md",
            "quote": "El conjunto de datos — cuando esta sección lo posee"
          }
        }
      ],
      "requires_declarations": [],
      "citations": "resolution",
      "optional": true
    },
    {
      "id": "es-assessment",
      "requires_facts": [
        {
          "value": "contributions",
          "source": {
            "file": "sections/02-experimental-setup.md",
            "quote": "Qué propiedad afirma cada contribución — si fue prometida, aquí es donde se nombra su instrumento"
          }
        },
        {
          "value": "experimental-design",
          "source": {
            "file": "sections/02-experimental-setup.md",
            "quote": "El diseño experimental — los métodos competidores, los ejes y los criterios del corpus construido a propósito, establecidos como un único protocolo de comparación"
          }
        },
        {
          "value": "gap",
          "source": {
            "file": "sections/02-experimental-setup.md",
            "quote": "La brecha — que ninguna referencia estándar mide lo que se afirma, razón por la cual existe el corpus construido a propósito"
          }
        }
      ],
      "requires_declarations": [],
      "citations": "resolution",
      "after": [
        {
          "target": "experimental-setup.es-dataset",
          "source": {
            "file": "sections/02-experimental-setup.md",
            "quote": "Su única dependencia que NO es interna son los datos que debe mostrar entrando, que residen en `es-dataset` cuando el conjunto de datos pertenece a esta sección"
          }
        },
        {
          "target": "materials-and-methods.mm-proposal",
          "source": {
            "file": "sections/02-experimental-setup.md",
            "quote": "Qué propiedad afirma cada contribución — si fue prometida, aquí es donde se nombra su instrumento"
          }
        },
        {
          "target": "introduction.block-3",
          "source": {
            "file": "sections/02-experimental-setup.md",
            "quote": "La brecha — que ninguna referencia estándar mide lo que se afirma, razón por la cual existe el corpus construido a propósito"
          }
        },
        {
          "target": "related-work.rw-closing",
          "source": {
            "file": "sections/02-experimental-setup.md",
            "quote": "La brecha — que ninguna referencia estándar mide lo que se afirma, razón por la cual existe el corpus construido a propósito"
          }
        }
      ],
      "figure": {
        "ordered": false,
        "excludes": ["internal component of the proposal"],
        "caption_enumerates": true,
        "caption_decodes": false,
        "mandatory": true
      }
    },
    {
      "id": "es-training-details",
      "requires_facts": [
        {
          "value": "implementation",
          "source": {
            "file": "sections/02-experimental-setup.md",
            "quote": "La implementación de los experimentos y su configuración — lo que realmente se ejecutó"
          }
        }
      ],
      "requires_declarations": [],
      "citations": "none"
    }
  ]
}
---
# Configuración Experimental

**Extensión** 1020–4140 palabras · un preámbulo y dos subsecciones
**Contiene** las definiciones de las métricas, los métodos comparados y un diagrama de cierre
**No contiene** ningún resultado

Esta sección responde *¿obtendría yo sus números si ejecutara esto por mi cuenta?*. Convierte
el método en un protocolo: qué se mide, contra qué se mide y bajo qué
condiciones exactas. Cada número de la sección de resultados debe poder rastrearse hasta algo
declarado aquí.

La sección de métodos dice lo que el modelo **es**. Esta dice lo que se le **hizo**. Nada aquí se descubre: cada condición que esta sección enuncia ya estaba fijada cuando se ejecutaron los experimentos.

## Las dos subsecciones separan el diseño de la ejecución

**Evaluación y Comparación de Métodos es el diseño de la comparación. Detalles de Entrenamiento
es su ejecución.** Todo lo que responde a *qué se mide y contra qué* es
diseño. Todo lo que responde a *con qué valores y en qué máquina se ejecutó* es
ejecución. Son lo mismo antes y después de ejecutar.

La sección tiene dos subsecciones. Cuando los conjuntos de datos no pertenecen a la sección de
métodos, son el primer bloque de Evaluación y no una tercera subsección.

## Preámbulo

Un párrafo de 33–41 palabras, sin citas. Nombra los bloques que la sección
especifica, en orden.

## Subsección 1 — Evaluación y Comparación de Métodos

Siete bloques. El primero y los dos últimos son condicionales.

**1. Los conjuntos de datos** — solo cuando la sección de métodos no los posee. Primero.

**2. El anuncio de la división** — cuando el marco tiene dos mitades disímiles.
Cada mitad hace entonces su propio recorrido por los bloques que siguen.

**3. Los ejes de comparación.** Las arquitecturas, backbones o variantes sobre los que se
barre la comparación, cada uno con su tabla de estructura — capas, dimensiones, número de parámetros
— y su cita. El eje es tan parte del protocolo como la métrica.

**4. Los métodos competidores.** Un elemento de lista cada uno, una cita cada uno y, cuando sea
posible, **su propia ecuación definitoria**. No se limite a nombrar una línea base: formalícela.
Un competidor escrito como un objetivo no deja duda sobre qué versión se ejecutó.

**5. Las métricas cuantitativas.** Cada una definida por una ecuación numerada, con su glosario
de símbolos inmediatamente **después** de la ecuación, no antes. Este es el
lugar con mayor densidad de ecuaciones del artículo fuera de la sección de métodos, y cada ecuación
aquí es la definición de una métrica.

**Cada instrumento se nombra bajo la propiedad que mide**, usando las mismas palabras
que el planteamiento del problema y la contribución usaron para esa propiedad. Un sinónimo rompe
la cadena que va del problema a la evidencia.

**6. Los instrumentos cualitativos o complementarios.** Las técnicas de visualización o de atribución
que respaldan las afirmaciones que ninguna métrica mide, cada una con su cita. Estas
son las que responden a las propiedades que una contribución prometió y que una métrica no puede alcanzar.

**7. El corpus de evaluación construido a propósito** — solo cuando ninguna referencia estándar mide
lo que se afirma. Descríbalo aquí: su tamaño, su composición y una tabla de
ejemplos. Sin él, la métrica de esa mitad no significa nada.

### Qué se cita aquí

**Una cita por objeto comparado.** Una por método competidor, una por eje o
arquitectura barrida, una por instrumento cualitativo y una por métrica **no estándar**.

**Las métricas estándar llevan una ecuación, no una cita.** La misma asimetría que en la
sección de métodos: lo que se toma prestado se cita, lo que es convencional se define.

## Subsección 2 — Detalles de Entrenamiento

El bloque de reproducibilidad. Tiempo pasado, voz pasiva para el procedimiento. Seis espacios.

**1. Preprocesamiento y exclusiones.** Qué se filtró, descartó o remuestreó, y
por qué. Indique lo que se desechó antes de indicar lo que se conservó.

**2. El protocolo de partición.** Las divisiones, la estrategia de validación cruzada, la
estratificación.

**3. El optimizador y el calendario.**

**4. La búsqueda de hiperparámetros.** La herramienta, el muestreador, **la semilla**, el objetivo
que se minimiza y el rango de búsqueda por modelo. Nombrar la semilla y la configuración
del podador es el nivel en el que una ejecución se vuelve reproducible.

**5. Control de fuga de información.** Una oración explícita que indique que todo lo que requería una
referencia usó información únicamente de la partición de entrenamiento.

**6. Software y hardware.** Versión del lenguaje, versión del framework, versiones de las bibliotecas,
el entorno y el acelerador por modelo — obligatorio siempre que se reporten tiempos
en cualquier parte.

**Un valor viene con la razón por la que tiene ese valor.** Las cotas establecidas empíricamente
se enuncian junto con lo que la cota garantiza. La forma de un objetivo se justifica en
la sección de métodos; un valor dentro de una forma fija se justifica aquí.

**Cada parámetro ajustable tiene trazabilidad.** Un hiperparámetro nombrado aquí debe ser un símbolo declarado en
la sección de métodos.

**La tabla completa de parámetros puede ir a un apéndice**, conservando en el cuerpo solo los
valores sobre los que se razonó. Ese es el uso correcto de un apéndice: el cuerpo
contiene lo que tiene una razón, el apéndice contiene lo que debe poder consultarse.

## Cada artefacto se referencia antes de aparecer

Cualquier objeto numerado — figura, tabla o panel — se referencia en el cuerpo **antes**
de aparecer, y la referencia apunta al subelemento exacto cuando el artefacto tiene
partes. Un artefacto que aparece sin referencia previa está mal ubicado o está muerto.

## Las figuras y tablas aquí son protocolo, nunca resultados

Nada en esta sección reporta un desempeño. Sus figuras ilustran el protocolo —
el calendario que se usó, el espectro de la entrada, la estructura del diseño —
y sus tablas contienen las arquitecturas de cada eje y los valores de los parámetros.

## El diagrama de cierre

La sección cierra con un diagrama, y **es el traspaso a la sección de resultados**.
Lo que el lector debe llevar consigo es el cruce, no los valores: los valores se
consultan cuando se necesitan, el cruce debe tenerse en mente para leer una tabla de resultados.

Muestra:

- qué datos entran;
- contra qué métodos se ejecuta la comparación;
- sobre qué ejes se barre;
- qué métrica sale de cada cruce;
- dónde se acoplan los instrumentos cualitativos;
- **la unidad de repetición** — sobre qué se promedia un único número reportado, y
  a través de qué se calcula su dispersión.

La propuesta es una fila del cruce, no el centro de la figura.

Esa unidad de repetición es el único elemento de ejecución admitido en el diagrama.
Sin ella, una celda del diagrama no puede leerse como una celda de una tabla. Todo lo demás
sobre la ejecución permanece en Detalles de Entrenamiento, que es donde se consulta.

**Su obligación con la sección de resultados:** cada tabla y cada figura de allí debe poder
ubicarse en este diagrama. Una celda reportada que el diagrama no contiene es una celda que el
diseño nunca declaró.

**Separación respecto del diagrama de métodos.** El diagrama de métodos muestra el método; este
muestra el experimento. La prueba: **ningún conjunto de datos ni ninguna línea base aparece en el
diagrama de métodos, y ningún componente interno de la propuesta aparece en este.** Una
caja que aparece en ambos significa que uno de ellos está mal.

## Entradas

### Entradas externas

| Entrada | Desbloquea |
|---|---|
| El **conjunto de datos** — cuando esta sección lo posee | `es-dataset` |
| Los **métodos competidores** — la lista de líneas base establecida en el estado del arte | `es-assessment` |
| Los **ejes** — sobre qué se barre la comparación | `es-assessment` |
| El **corpus construido a propósito** — que ninguna referencia estándar mide lo que se afirma | `es-assessment` |
| El **diseño experimental** — los métodos competidores, los ejes y los criterios del corpus construido a propósito, establecidos como un único protocolo de comparación | `es-assessment` |
| La **implementación** de los experimentos y su configuración — lo que realmente se ejecutó | `es-training-details` |

### Cadena interna

| Bloque | Depende de |
|---|---|
| `experimental-setup.es-assessment` — el panel "qué datos entran" del diagrama de cierre | `experimental-setup.es-dataset` — el bloque del conjunto de datos, cuando esta sección lo posee |
| `experimental-setup.es-assessment` — Qué propiedad afirma cada contribución — si fue prometida, aquí es donde se nombra su instrumento | `materials-and-methods.mm-proposal` — las contribuciones enumeradas para las que se nombra el instrumento |
| `experimental-setup.es-assessment` — La brecha — que ninguna referencia estándar mide lo que se afirma, razón por la cual existe el corpus construido a propósito | `introduction.block-3` — la brecha conjunta, condensada allí |
| `experimental-setup.es-assessment` — La brecha — que ninguna referencia estándar mide lo que se afirma, razón por la cual existe el corpus construido a propósito | `related-work.rw-closing` — la brecha conjunta, desarrollada allí |

### Decisiones estructurales

- **Cuántos bloques tiene Evaluación** lo decide la ubicación del conjunto de datos
  ya decidida en la sección de métodos — una decisión estructural, no una
  dependencia de un bloque específico.
- **El diagrama de cierre** es el cruce declarado por todo lo que Evaluación
  ya contiene, más la unidad de repetición — una regla de composición interna
  dentro del propio `es-assessment`. Su única dependencia que NO es interna son
  los datos que debe mostrar entrando, que residen en `es-dataset` cuando el
  conjunto de datos pertenece a esta sección; esa es una fila de la cadena de arriba, no una
  decisión estructural.

## Descalificadores

- Una métrica nombrada pero no definida.
- Un glosario de métrica ubicado antes de su ecuación en lugar de después.
- Una cita en una métrica estándar, o una cita faltante en una no estándar.
- Un método competidor nombrado sin cita, o nombrado sin ser formalizado
  cuando existe una formalización.
- Un eje barrido sin declarar su estructura.
- Una propiedad afirmada por una contribución sin un instrumento nombrado aquí.
- Un instrumento nombrado con un nombre distinto al que la propiedad que mide lleva en
  el planteamiento del problema y en la contribución.
- Un artefacto que aparece antes de cualquier referencia a él, o al que nada referencia en
  absoluto.
- Una referencia a un artefacto completo cuando el valor está en una de sus partes.
- Un corpus construido a propósito usado sin ser descrito.
- Un hiperparámetro sin valor, o un valor que no coincide con la configuración que se
  ejecutó.
- Un parámetro ajustable que no existe en la sección de métodos.
- Una semilla, división o número de repeticiones omitido.
- Hardware omitido mientras se reportan tiempos.
- Ninguna declaración de control de fuga de información.
- Un resultado, una comparación medida o una cifra de desempeño.
- La ausencia del diagrama de cierre.
- Una tabla o figura de resultados que no puede ubicarse en el diagrama de cierre.
- Una caja compartida entre el diagrama de cierre y el diagrama de métodos.
- Cualquier elemento de ejecución en el diagrama de cierre distinto de la unidad de repetición.
- La tabla completa de parámetros en el cuerpo cuando solo se razonó sobre algunos valores, o
  una tabla de apéndice que contradice el cuerpo.
