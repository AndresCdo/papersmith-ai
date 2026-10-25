---
{
  "section": "back-matter",
  "position": 10,
  "mode": {
    "value": "transposition",
    "source": {
      "file": "sections/10-back-matter.md",
      "quote": "Cada bloque aquí es un hecho externo, no una decisión."
    }
  },
  "blocks": [
    {
      "id": "bm-author-contributions",
      "requires_facts": [],
      "requires_declarations": [
        {
          "value": "author-roles",
          "source": {
            "file": "sections/10-back-matter.md",
            "quote": "Los author-roles — la lista de autores y los roles confirmados de cada autor"
          }
        }
      ],
      "citations": "none"
    },
    {
      "id": "bm-funding",
      "requires_facts": [],
      "requires_declarations": [
        {
          "value": "grant-title",
          "source": {
            "file": "sections/10-back-matter.md",
            "quote": "El grant-title y el grant-code — el título registrado del proyecto de financiamiento, el financiador y el código"
          }
        },
        {
          "value": "grant-code",
          "source": {
            "file": "sections/10-back-matter.md",
            "quote": "El grant-title y el grant-code — el título registrado del proyecto de financiamiento, el financiador y el código"
          }
        }
      ],
      "citations": "none"
    },
    {
      "id": "bm-data-availability",
      "requires_facts": [],
      "requires_declarations": [
        {
          "value": "repository-url",
          "source": {
            "file": "sections/10-back-matter.md",
            "quote": "La repository-url — la URL del repositorio del proyecto y la fecha en que se verificó"
          }
        }
      ],
      "citations": "none"
    },
    {
      "id": "bm-conflicts-of-interest",
      "requires_facts": [],
      "requires_declarations": [],
      "citations": "none"
    },
    {
      "id": "bm-acknowledgments",
      "requires_facts": [],
      "requires_declarations": [],
      "citations": "none",
      "optional": true,
      "after": [
        {
          "target": "back-matter.bm-funding",
          "source": {
            "file": "sections/10-back-matter.md",
            "quote": "Presente solo cuando hay un proyecto o institución que agradecer que no esté ya nombrado en el financiamiento."
          }
        }
      ]
    },
    {
      "id": "bm-appendices",
      "requires_facts": [],
      "requires_declarations": [],
      "citations": "none",
      "optional": true
    }
  ]
}
---
# Material final

El bloque administrativo que va después de las conclusiones y antes de las referencias.
No es prosa científica: es la superficie de rendición de cuentas del artículo: quién hizo qué,
quién pagó, dónde están los datos y el código, y qué podría sesgar el trabajo.

Cada bloque es una etiqueta en línea en negrita seguida de prosa. Sin encabezados de sección, sin
subsecciones. Esta es la parte más mecánica del artículo y la que con más probabilidad estará
mal en el envío, porque nadie la trata como escritura.

## Los bloques, en este orden

| Bloque | Obligatorio | Palabras |
|---|---|---|
| Contribuciones de los autores | sí | 37–44 |
| Financiamiento | sí | 55 por proyecto |
| Declaración de disponibilidad de datos | sí | 7–22 |
| Conflictos de interés | sí | una oración |
| Agradecimientos | solo si hay un proyecto que agradecer | ~25 |
| Apéndices | solo si el artículo los necesita | — |

## Contribuciones de los autores

Una fórmula, por eso su extensión apenas varía. Los roles CRediT, separados por
punto y coma, cada uno seguido de las iniciales de los autores que lo desempeñaron, separadas por comas
con *y* antes de la última. Luego la oración de cierre habitual que indica que todos los
autores han leído y aceptado la versión publicada.

**Cada autor aparece en al menos un rol.** Los roles son los que cada autor
confirmó, no los inferidos a partir del trabajo.

## Financiamiento

Una entrada por subvención. Cada una lleva el **título registrado exacto** del proyecto, en su
idioma original, el financiador y el código de la subvención. Cuando una subvención apoya a un autor
específico y no al trabajo en su conjunto, nombre a ese autor junto con ella.

Los códigos de subvención se copian de los registros de financiamiento, nunca se reescriben de memoria.

## Declaración de disponibilidad de datos

La URL del repositorio más la fecha en que se verificó. La URL debe resolver, y debe
contener el código que produjo los números reportados.

Cuando los datos no pueden publicarse, dígalo en una línea e indique la vía para solicitarlos.
No remita a un repositorio que contiene solo código dando a entender que contiene los datos.

Indique qué es público y qué no lo es: son afirmaciones distintas.

## Conflictos de interés

Una oración que declara que no existen.

El único caso que requiere más: cuando un autor está afiliado a una organización con
interés en los resultados (normalmente la que suministró los datos), nombre la
afiliación explícitamente y repita la declaración para ese autor. El silencio sobre una
afiliación conocida es el fallo que este bloque existe para prevenir.

## Agradecimientos

Presente solo cuando hay un proyecto o institución que agradecer que no esté ya
nombrado en el financiamiento. Una o dos oraciones.

## Apéndices

Se usan cuando un material es necesario para reproducir el trabajo pero rompería el flujo de
la sección que lo necesita: artefactos textuales, o una tabla completa de parámetros cuando la
configuración experimental contiene solo los valores que se razonaron.

Identificados con letras, con subsecciones numeradas bajo su letra. **Cada apéndice se referencia
desde la sección del cuerpo que lo necesita**; uno que nada referencia es peso muerto.

Si el artículo tiene apéndices o no se decide para cada artículo.

## Entradas

Cada bloque aquí es un hecho externo, no una decisión. Nada de ello se deriva del
artículo.

### Entradas externas

| Entrada | Desbloquea |
|---|---|
| Los **author-roles** — la lista de autores y los roles confirmados de cada autor | `bm-author-contributions` |
| El **grant-title** y el **grant-code** — el título registrado del proyecto de financiamiento, el financiador y el código | `bm-funding` |
| La **repository-url** — la URL del repositorio del proyecto y la fecha en que se verificó | `bm-data-availability` |
| Cualquier afiliación de un autor con una organización interesada | `bm-conflicts-of-interest` |
| El proyecto o la institución que agradecer | `bm-acknowledgments` |
| Las secciones del cuerpo que necesiten uno | `bm-appendices` |

### Cadena interna

| Bloque | Depende de |
|---|---|
| `back-matter.bm-acknowledgments` — presente solo cuando hay un proyecto o institución que agradecer que no esté ya nombrado en el financiamiento | `back-matter.bm-funding` — las entradas de financiamiento que ya nombran cualquier proyecto o institución acreditados allí |

## Descalificadores

- Un autor sin rol.
- Un rol atribuido sin que el autor lo confirme.
- Un título o código de subvención reproducido de memoria en lugar de copiado.
- Una URL de repositorio que no resuelve, o que contiene código incapaz de producir los
  números reportados.
- Una fecha de acceso faltante en la URL.
- Una declaración de disponibilidad de datos que afirma que son públicos datos que no lo son.
- Una afiliación interesada conocida sin declarar.
- Un apéndice que ninguna sección del cuerpo referencia.
- Contenido de un apéndice que contradice la configuración experimental.
