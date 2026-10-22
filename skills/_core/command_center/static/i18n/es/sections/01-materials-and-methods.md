---
{
  "section": "materials-and-methods",
  "position": 5,
  "mode": {
    "value": "transposition",
    "source": {
      "file": "sections/01-materials-and-methods.md",
      "quote": "La propuesta ya existe."
    }
  },
  "blocks": [
    {
      "id": "mm-preamble",
      "requires_facts": [],
      "requires_declarations": [],
      "citations": "none",
      "after": [
        {
          "target": "materials-and-methods.mm-proposal",
          "source": {
            "file": "sections/01-materials-and-methods.md",
            "quote": "Nombra las subsecciones que siguen y su orden."
          }
        }
      ]
    },
    {
      "id": "mm-dataset",
      "requires_facts": [
        {
          "value": "dataset",
          "source": {
            "file": "sections/01-materials-and-methods.md",
            "quote": "El conjunto de datos — cuando esta sección es su dueña"
          }
        }
      ],
      "requires_declarations": [],
      "citations": "resolution",
      "optional": true
    },
    {
      "id": "mm-borrowed-machinery",
      "requires_facts": [
        {
          "value": "formulation",
          "source": {
            "file": "sections/01-materials-and-methods.md",
            "quote": "La formulación matemática de la propuesta"
          }
        }
      ],
      "requires_declarations": [],
      "citations": "resolution"
    },
    {
      "id": "mm-proposal",
      "requires_facts": [
        {
          "value": "formulation",
          "source": {
            "file": "sections/01-materials-and-methods.md",
            "quote": "La formulación matemática de la propuesta"
          }
        }
      ],
      "requires_declarations": [],
      "citations": "resolution",
      "produces_facts": [
        {
          "value": "contributions",
          "source": {
            "file": "sections/01-materials-and-methods.md",
            "quote": "Esta sección define las contribuciones."
          }
        }
      ],
      "after": [
        {
          "target": "materials-and-methods.mm-borrowed-machinery",
          "source": {
            "file": "sections/01-materials-and-methods.md",
            "quote": "enunciar la propuesta como un delta sobre la maquinaria prestada, con una referencia explícita a la ecuación anterior por su número"
          }
        },
        {
          "target": "materials-and-methods.mm-dataset",
          "source": {
            "file": "sections/01-materials-and-methods.md",
            "quote": "La propuesta es siempre la última subsección. Sin excepción."
          }
        }
      ],
      "figure": {
        "components_from": "contributions",
        "ordered": true,
        "excludes": ["dataset", "baseline"],
        "caption_enumerates": true,
        "caption_decodes": true,
        "mandatory": true
      }
    }
  ]
}
---
# Materiales y métodos

**Extensión** 560–3950 palabras · 2 a 5 subsecciones
**Contiene** la maquinaria prestada, la propuesta y un diagrama de síntesis
**No contiene** ningún resultado, número medido ni comparación

Esta sección define las contribuciones. Aquí nombra cada una y le da su
definición formal, en la notación que reutiliza todo lo que viene después; la introducción
recibe esa lista y se redacta a partir de ella.

## Aquí no se decide nada

La propuesta ya existe. Esta sección no la elige, no la mejora ni argumenta
a su favor: traslada una formulación existente a esta estructura. Donde la sección
parece estar decidiendo algo, está informando una decisión tomada en otro lugar.

## Preámbulo

Un párrafo de unas 40 palabras, dos oraciones, sin citas. Nombra las
subsecciones que siguen y su orden. Nada más.

## Orden de las subsecciones

Tres posiciones. La tercera es invariante.

| Posición | Subsecciones | Palabras cada una |
|---|---|---|
| 1 — El conjunto de datos, cuando esta sección es su dueña | 1 | 550–1000 |
| 2 — La maquinaria prestada | 1 a 3 | 180–1480 |
| 3 — **La propuesta** | 1 | 380–1420 |

**La ubicación del conjunto de datos es una decisión estructural, y se toma una sola vez.** Si el
conjunto de datos pertenece a esta sección, va primero, y la sección abre con los datos. Si
pertenece en cambio a la configuración experimental, esta sección empieza directamente con la
maquinaria y se mantiene puramente formal, sin ninguna figura distinta del diagrama
de la propuesta. La decisión cambia el contrato de ambas secciones, por lo que se registra en lugar
de improvisarse.

**La propuesta es siempre la última subsección.** Sin excepción.

## Posición 1 — El conjunto de datos

De 6 a 12 párrafos. Una o dos figuras: protocolo de adquisición o muestras
representativas. Cero a dos tablas: listas de variables. Pocas o ninguna ecuación.

Se abre según de quién sean los datos:

- **Datos propios o construidos:** procedencia y período de tiempo en la primera oración, luego
  el objetivo que justifica esas variables.
- **Datos públicos:** por qué *estos* conjuntos responden a la pregunta y qué los hace diferentes
  entre sí.

**Indique lo que se descartó antes de indicar lo que se conservó**: exclusiones, filtros
de calidad, registros eliminados.

**Aquí se paga la deuda de crédito de la introducción.** Un conjunto de datos nombrado en
la introducción sin referencia se nombra aquí con una.

## Posición 2 — La maquinaria prestada

De una a tres subsecciones, cada una un cuerpo de teoría existente que la propuesta necesita. Aquí
reside el grueso de las matemáticas del artículo.

**Ordenada de modo que cada subsección use solo símbolos que las anteriores declararon.** Es
una cadena de notación, no una lista de temas.

**Cada subsección abre declarando la notación, antes de cualquier ecuación.** Ninguna subsección
matemática abre con una ecuación. Use notación por comprensión con un dominio de índice
explícito para una colección.

**Desarrollada solo hasta la profundidad con que la propuesta la usa.** Más que eso es trabajo relacionado
que se filtra.

## Posición 3 — La propuesta

Siempre al final. La subsección menos citada del artículo.

**1. Apertura: nombrar el método y enunciar su contexto.** Donde sea posible, enunciar la
propuesta como un delta sobre la maquinaria prestada, con una referencia explícita a la
ecuación anterior por su número, para que el lector sepa exactamente qué cambió respecto de
lo que acaba de leer.

**2. Su propia notación**, si la propuesta introduce símbolos que la maquinaria no
tenía.

**3. Las contribuciones, definidas, en el orden que esta sección establece.** La
lista de la introducción sigue este orden, nunca al revés. Cada una: qué
introduce, su ecuación y el símbolo que deja disponible para la siguiente. Cada
contribución se define aquí y en ningún otro lugar.

**Cada contribución se define bajo la propiedad que aporta**, nombrada con las mismas
palabras que el planteamiento del problema usa para esa propiedad. La lista de contribuciones de la introducción
reutiliza luego ese nombre exacto. Ese nombre compartido es lo que hace que la cadena desde el
problema hasta la evidencia sea trazable y no simplemente plausible.

**4. La combinación general.** La única expresión que reúne todas las contribuciones:
la suma, el objetivo compuesto o lo que corresponda al caso. Dos
posiciones, ambas admisibles: al final, construyendo las piezas y cerrando con la
integración; o al inicio, enunciando el objetivo completo con sus restricciones y
luego descomponiéndolo.

Este es el único lugar del artículo donde todas las contribuciones aparecen juntas, y
es la recompensa de la cadena de notación: **cada símbolo que contiene debe remontarse a una
declaración previa.** Uno que no lo haga significa que la cadena se rompió antes.

Cuando la contribución es un sistema en lugar de una formulación, la combinación la
llevan la enumeración de etapas y el diagrama. Allí el diagrama no es un
resumen: es la combinación misma.

**La lista de contribuciones debe poder leerse como una lista, en el propio orden del diagrama.** Dos
estructuras lo cumplen, y solo una de ellas se necesita en cada caso:

- **Cada contribución es su propia subsección.** El seccionamiento ya es la lista
  ordenada: sus encabezados nombran las contribuciones, en orden, y el lector las encuentra como
  estructura en lugar de como prosa. No se requiere nada más, y una lista de `\item`
  que repita esos mismos encabezados unas líneas después es redundancia, no un mandato.
- **Las contribuciones se integran en la prosa.** Entonces la lista no tiene otra forma, y
  se escribe una inmediatamente antes del puntero de cierre: un `\item` de LaTeX por
  contribución, nombrándola exactamente como se definió arriba, en el propio orden del diagrama,
  nada más por ítem.

En cualquier caso, lo que el propio Components Check de la sección contrasta con el diagrama es
esa lista ordenada de nombres, sea cual sea de las dos la que la contenga.

**5. El cierre: puntero y diagrama de síntesis.** Obligatorio. La última oración en prosa
remite a la figura por su número y dice qué sintetiza; la figura sigue
inmediatamente.

**Opcional, y solo donde haya algo que decir:** una cláusula sobre convergencia o
estabilidad, que distinga la consistencia del estimador de la convergencia
empírica del entrenamiento. Pertenece aquí y no a la configuración experimental: esa
sección es procedimiento en tiempo pasado, y un argumento de convergencia es una afirmación en tiempo presente
sobre la formulación.

### El diagrama de síntesis

- **Es la forma visual de la lista de contribuciones**: contiene exactamente los mismos
  componentes, en el mismo orden, con los mismos nombres que les da la propia lista
  de esta sección.
- **La leyenda los enumera en ese orden** y decodifica todo lo que la figura
  codifica: si hay colores, la leyenda dice qué significa cada uno.
- **Muestra el método, no el experimento.** En él no aparece ningún conjunto de datos ni ninguna línea base;
  esos pertenecen al propio diagrama de la configuración experimental. Un recuadro que aparece en ambos
  significa que uno de los dos está mal.
- **El Components Check al que se somete este diagrama lo compara con la propia lista
  de este mismo bloque.** Es una deriva interna del bloque, nunca una corroboración
  entre secciones: no se consulta nada fuera de este bloque.

## Todo artefacto se referencia antes de aparecer

Cualquier objeto numerado (figura, tabla o panel) se referencia en el cuerpo **antes** de
que aparezca, y el puntero apunta al subelemento exacto cuando el artefacto tiene
partes. Un artefacto que aparece sin referencia previa está mal ubicado o muerto.

## Continuidad

Todo debe leerse como continuo, y la continuidad aquí es verificable, no una sensación.

**Cada símbolo se remonta a su declaración.** Cada subsección usa solo lo que las
anteriores declararon, y la propuesta abre nombrando lo que toma de la
maquinaria.

**Ningún símbolo se reutiliza para una cantidad distinta.** Cuando dos cantidades naturalmente
coincidirían en la misma letra, sepárelas con un diacrítico y declare ambas en la
misma oración, para que el lector vea la distinción una sola vez.

**Un diacrítico marca una relación con un objeto ya declarado**, nunca es decoración.
Cuatro usos:

- el mismo objeto tras una transformación;
- un estimador de una cantidad declarada;
- una versión normalizada de una cantidad declarada;
- la desambiguación de dos cantidades distintas que compartirían una letra.

## La extensión cuenta prosa, nunca matemáticas

Todo conteo de palabras de este contrato mide la prosa. Una ecuación destacada, su
etiqueta y su número no son prosa y no cuentan para ninguna extensión aquí.

**Una formulación cuyas matemáticas son largas no es por ello una formulación que deba
recortarse.** Las matemáticas se trasladan tal como están; lo que la extensión restringe es lo que se
escribe a su alrededor: la notación que declara sus símbolos, la oración que
anuncia cada expresión y la lectura que la sigue. Cuando una subsección excede
su extensión, lo que se ajusta es la prosa, nunca la derivación.

Una sección que omite pasos de las matemáticas de su propia fuente para ajustarse a un presupuesto de palabras ha
malinterpretado el presupuesto. Nada en este contrato lo autoriza.

## Ecuaciones: destacar y numerar son dos decisiones separadas

**Destacar por legibilidad.** Una expresión que no puede leerse en línea (de varias líneas,
con restricciones, con sumas sobre índices) se destaca. Lo que se lee en una línea
corrida permanece en el texto.

**Numerar por referencia.** Numérela si se va a referenciar por número más adelante, si
define una contribución o si es la combinación general. Una ecuación destacada
que nadie volverá a nombrar se destaca sin número.

Numerar por reflejo es el fallo común: produce largas series de expresiones
numeradas que ninguna oración del artículo menciona jamás.

**Las ecuaciones referenciadas se nombran por su número** entre subsecciones y entre secciones.
Esa referencia cruzada es lo que hace verificable la cadena de notación.

**Una referencia mira hacia atrás, nunca a una línea más arriba.** La oración que sigue a una
ecuación destacada expresa lo que se desprende de ella (la consecuencia, la lectura, el
paso siguiente) con sus propias palabras. Abrir esa oración nombrando la ecuación que el lector
acaba de terminar es redundancia, no una referencia cruzada. Lo mismo vale dentro de un
párrafo: un puntero por ecuación es suficiente, y un segundo en el mismo párrafo
no dice nada que el primero no haya dicho.

## Ambigüedad entre la ecuación y el código

Una ecuación puede estar escrita correctamente y aun así admitir dos lecturas: un objetivo
que suma sobre todas las clases cuando algunas están ausentes de un lote, una normalización cuyo
dominio no se enuncia.

**Donde una lectura es ambigua, la correcta se enuncia en el párrafo del
componente al que pertenece**, como una cláusula, no como un párrafo aparte. Cuál lectura es
correcta es un hecho sobre la implementación, no sobre las matemáticas: se lee de
lo que el código calcula.

**Lo que es un valor o un procedimiento no pertenece aquí**: tamaño de lote, tasa de aprendizaje,
calendario, hardware. Esos son de la configuración experimental.

**Pero todo parámetro ajustable que el método expone se nombra aquí**, aunque su valor se fije en
otro lugar. La configuración experimental no puede introducir un parámetro que no exista
en esta sección.

**El mismo corte se aplica a la elección de un parámetro.** Si la elección cambia la *forma* del
objetivo, se enuncia aquí como una cláusula en el párrafo del componente. Si es un
valor elegido dentro de una forma fija, pertenece a la configuración experimental.

## Citas

La densidad de citas cae bruscamente aquí: aproximadamente de cuatro a diez veces menor que en la
introducción. No es moderación: la introducción cita afirmaciones sobre el campo,
y esta sección cita **objetos**.

**La cita se adjunta al objeto que acredita, dondequiera que ese objeto esté en la
oración.** Esto difiere de la introducción, donde la cita respalda una afirmación
y por tanto cierra la oración. Cuando lo que se acredita aquí es una afirmación y no
un objeto, también cierra la oración.

**Un objeto matemático prestado llega con su procedencia adjunta a la oración
que lo anuncia, antes de que aparezca la ecuación.** El lector ve de quién es la definición
en el momento de leerla, no al final del párrafo.

Se citan cinco cosas:

1. el origen de una definición o un estimador prestados;
2. el origen de un algoritmo o componente con nombre;
3. la procedencia de los datos: quién los publica y dónde están disponibles;
4. la justificación de que una variable importa, en la subsección del conjunto de datos;
5. una propiedad afirmada sobre el método que otros ya establecieron.

**Lo prestado se cita, lo propio no.** Ninguna ecuación de la propuesta lleva una cita.

## Evitar volver a motivar

El riesgo concreto de redundancia en esta sección es la motivación. El problema se planteó en
la introducción y la brecha se cerró antes de esta sección. Aquí una contribución se
**define**, no se justifica. Una cláusula de propósito por contribución es suficiente; un párrafo
que explique por qué importa el problema es material repetido.

## Entradas

Nada aquí espera a un experimento. Pero sí espera a que exista el código.

### Entradas externas

| Entrada | Desbloquea |
|---|---|
| La **formulación matemática** de la propuesta | `mm-borrowed-machinery`, `mm-proposal` |
| El **conjunto de datos** — cuando esta sección es su dueña | `mm-dataset` |

### Cadena interna

| Bloque | Depende de |
|---|---|
| `materials-and-methods.mm-proposal` — enunciada como un delta sobre la maquinaria prestada, con una referencia explícita a la ecuación anterior por su número | `materials-and-methods.mm-borrowed-machinery` — la teoría prestada cuyas ecuaciones declaradas referencia la propuesta |
| `materials-and-methods.mm-proposal` — siempre la última subsección, sin excepción | `materials-and-methods.mm-dataset` — la subsección del conjunto de datos, cuando esta sección es su dueña |
| `materials-and-methods.mm-preamble` — nombra las subsecciones que siguen y su orden | `materials-and-methods.mm-proposal` — la última de las subsecciones que debe nombrar, por lo que el preámbulo se escribe una vez que existe cada subsección que anuncia |

### Decisiones estructurales

- **La lectura correcta de una ecuación ambigua** la decide la
  implementación: lo que el código calcula, no lo que dice la ecuación. Esta
  es una decisión registrada en el propio párrafo del componente afectado, no una
  dependencia de ningún otro bloque.

## Descalificadores

- Un símbolo usado sin haber sido declarado, o declarado dos veces con significados distintos.
- Dos cantidades distintas que comparten una letra sin un diacrítico que las separe, o un
  diacrítico que no marca ninguna relación con un objeto ya declarado.
- Un símbolo en la combinación general que no se remonta a ninguna declaración previa.
- Que la propuesta no sea la última subsección.
- Una contribución definida aquí que la introducción no nombró, o nombrada allí y
  no definida aquí.
- Contribuciones en un orden distinto del que les dio la introducción.
- La ausencia del diagrama de síntesis.
- La lista de contribuciones no legible en ninguna de las dos formas (ni una subsección por
  contribución ni una lista ordenada inmediatamente antes del puntero de cierre), o una
  lista escrita cuando las contribuciones ya son subsecciones.
- Un conjunto de datos o una línea base que aparece en el diagrama de síntesis.
- Una contribución definida con un nombre distinto de la propiedad que aporta
  en el planteamiento del problema y en la introducción.
- Un parámetro usado por la configuración experimental que no se nombra en ninguna parte aquí.
- Un artefacto que aparece antes de cualquier referencia a él, o que nada referencia en
  absoluto.
- Un puntero a un artefacto completo cuando el valor está en una de sus partes.
- Un diagrama cuyos componentes difieren en número, orden o nombre de la lista
  de contribuciones.
- Una leyenda que no decodifica lo que la figura codifica.
- Teoría prestada desarrollada más allá de la profundidad con que la propuesta la usa.
- Una ecuación destacada y numerada que ninguna oración referencia nunca, que no define ninguna
  contribución y que no es la combinación general.
- Una subsección matemática que abre con una ecuación en lugar de con notación.
- Una ecuación referenciada por número en la oración inmediatamente posterior a su propia
  presentación, o referenciada dos veces por número dentro de un mismo párrafo.
- Una ecuación ambigua que queda con ambas lecturas abiertas.
- Un tamaño de lote, una tasa de aprendizaje, un calendario o un detalle de hardware enunciado aquí.
- Un argumento de convergencia trasladado a la configuración experimental.
- Una cita en una ecuación de la propuesta.
- Una definición prestada cuya oración de anuncio no lleva cita.
- Un conjunto de datos descrito aquí y dejado sin referencia.
- Un párrafo que vuelve a motivar el problema.
- Un resultado, un número medido o una comparación.
