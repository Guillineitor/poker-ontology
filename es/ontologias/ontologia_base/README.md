# Ontología de Póker Texas Hold'em

Ontología escrita en OWL 2 DL que modela la estructura y los componentes de las partidas de Texas Hold'em Poker. Está redactada íntegramente en español y serializada en sintaxis Turtle (`.ttl`).

---

## Contenido

- Descripción general
- Perfil OWL y razonadores compatibles
- Estructura de la ontología
  - TBox: clases y propiedades
  - ABox: individuos
- Clases
  - Carta y sus subclases
  - Mano y tipos de mano
- Propiedades
  - Propiedades de Objeto
  - Propiedades de Datos
- Decisiones de diseño
  - Open World Assumption y clases cerradas
  - Propiedad shortcut `manoTienePar`
  - Disjunción entre tipos de mano

---

## Descripción general

| Atributo | Valor |
|---|---|
| IRI | `http://www.poker-ontology.org/poker` |
| Prefijo | `poker:` |
| Versión | `2.0.0` |
| Perfil OWL | OWL 2 DL |
| Serialización | Turtle (`.ttl`) |
| Idioma | Español |

La ontología modela los elementos fundamentales de una partida de Texas Hold'em: la baraja de 52 cartas (organizadas por palo y rango), la noción de mano de 5 cartas, y los diez tipos de mano estándar del póker, definidos como clases OWL con restricciones de clasificación automática.

---

## Perfil OWL y razonadores compatibles

La ontología utiliza construcciones de **OWL 2 DL**: cardinalidades calificadas (`owl:minQualifiedCardinality`), valores nominales (`owl:hasValue`), enumeraciones (`owl:oneOf`), intersecciones, uniones y restricciones de rango universal (`owl:allValuesFrom`).

Razonadores compatibles con OWL 2 DL:

| Razonador | Versión mínima recomendada | Notas |
|---|---|---|
| **HermiT** | 1.4.x | Recomendado; integrado en Protégé |
| **Openllet** | 2.6.x | Fork activo de Pellet; compatible con OWL API 5 |
| **JFact** | 5.x | Port Java puro de FaCT++ |

Razonadores **no compatibles** por perfil: ELK y Snorocket (solo OWL 2 EL; no soportan cardinalidades calificadas).

---

## Estructura de la ontología

### TBox: clases y propiedades

La TBox define el esquema conceptual del dominio. Incluye:

- Las clases `Palo` y `Rango` como enumeraciones cerradas.
- La clase `Carta` y sus 17 subclases (4 por palo + 13 por rango).
- La clase `Mano` y sus 9 subclases de tipo de mano, con sus `owl:equivalentClass`.
- 4 propiedades de objeto y 1 propiedad de datos.

### ABox: individuos

La ABox declara los 69 individuos concretos del dominio:

| Tipo | Cantidad | Descripción |
|---|---|---|
| `Palo` | 4 | Picas, Corazones, Diamantes, Tréboles |
| `Rango` | 13 | Dos (2) a As (14) |
| `Carta` | 52 | 13 rangos × 4 palos |

Todos los individuos están declarados `owl:AllDifferent` en tres bloques separados (palos, rangos, cartas), simulando la Unique Name Assumption bajo OWA.

---

## Clases

### Carta y sus subclases

```
Carta
├── CartaDeCorazones   ≡ tienePalo hasValue Corazones
├── CartaDeDiamantes   ≡ tienePalo hasValue Diamantes
├── CartaDePicas       ≡ tienePalo hasValue Picas
├── CartaDeTreboles    ≡ tienePalo hasValue Treboles
├── CartaDeDos         ≡ tieneRango hasValue Dos
├── CartaDeTres        ≡ tieneRango hasValue Tres
├── CartaDeCuatro      ≡ tieneRango hasValue Cuatro
├── CartaDeCinco       ≡ tieneRango hasValue Cinco
├── CartaDeSeis        ≡ tieneRango hasValue Seis
├── CartaDeSiete       ≡ tieneRango hasValue Siete
├── CartaDeOcho        ≡ tieneRango hasValue Ocho
├── CartaDeNueve       ≡ tieneRango hasValue Nueve
├── CartaDeDiez        ≡ tieneRango hasValue Diez
├── CartaDeJota        ≡ tieneRango hasValue Jota
├── CartaDeReina       ≡ tieneRango hasValue Reina
├── CartaDeRey         ≡ tieneRango hasValue Rey
└── CartaDeAs          ≡ tieneRango hasValue As
```

Las subclases por palo se usan en los clasificadores de `Color` y `EscaleraColor`. Las subclases por rango se usan en los clasificadores de `Par`, `Trio`, `Escalera`, `Poker` y `EscaleraReal`.

### Mano y tipos de mano

Una `Mano` contiene exactamente 5 cartas, expresado mediante cardinalidades mínima y máxima calificadas sobre `contieneCarta`.

Los tipos de mano se ordenan de menor a mayor fortaleza:

| # | Clase OWL | Nombre | Definición OWL resumida |
|---|---|---|---|
| 1 | `CartaAlta` | Carta Alta | `Mano ⊓ ∃contieneCarta.Carta`  |
| 2 | `Par` | Par | `Mano ⊓ (≥2 CartaDeDOS ⊔ ... ⊔ ≥2 CartaDeAs)` |
| 3 | `DoblePar` | Doble Par | `Mano ⊓ (≥2 manoTienePar)` |
| 4 | `Trio` | Trío | `Mano ⊓ (≥3 CartaDeDos ⊔ ... ⊔ ≥3 CartaDeAs)` |
| 5 | `Escalera` | Escalera | `Mano ⊓ (secuencia A-2-3-4-5 ⊔ ... ⊔ 10-J-Q-K-A)` |
| 6 | `Color` | Color | `Mano ⊓ (∀contieneCarta.CartaDeCorazones ⊔ ∀contieneCarta.CartaDeDiamantes ⊔ ∀contieneCarta.CartaDePicas ⊔ ∀contieneCarta.CartaDeTreboles)` |
| 7 | `Full` | Full | `Trio ⊓ DoblePar` |
| 8 | `Poker` | Póker | `Mano ⊓ (≥4 CartaDeDos ⊔ ... ⊔ ≥4 CartaDeAs)` |
| 9 | `EscaleraColor` | Escalera de Color | `Escalera ⊓ Color` |
| 10 | `EscaleraReal` | Escalera Real | `EscaleraColor ⊓ ∃contieneCarta.CartaDeDiez ⊓ ∃contieneCarta.CartaDeJota ⊓ ∃contieneCarta.CartaDeReina ⊓ ∃contieneCarta.CartaDeRey ⊓ ∃contieneCarta.CartaDeAs` |

`EscaleraReal` es subclase de `EscaleraColor`, no un tipo independiente; es el único caso particular de Escalera de Color que está nombrado en las reglas del póker.

`Full` y `EscaleraColor` se definen elegantemente como intersecciones de clases ya existentes: `Full ≡ Trio ⊓ DoblePar` y `EscaleraColor ≡ Escalera ⊓ Color`.

---

## Propiedades

### Propiedades de Objeto

| Propiedad | Dominio | Rango | Tipo | Descripción |
|---|---|---|---|---|
| `tienePalo` | `Carta` | `Palo` | `FunctionalProperty` | Asocia cada carta con su único palo. |
| `tieneRango` | `Carta` | `Rango` | `FunctionalProperty` | Asocia cada carta con su único rango. |
| `contieneCarta` | `Mano` | `Carta` | — | Relaciona una mano con las 5 cartas que la componen. |
| `manoTienePar` | `Mano` | `Rango` | — | Shortcut: indica qué rangos tienen al menos 2 cartas en la mano. Se agrega manualmente en el ABox. Usado por `DoblePar`. |


### Propiedades de Datos

| Propiedad | Dominio | Rango | Tipo | Descripción |
|---|---|---|---|---|
| `tieneValorRango` | `Rango` | `xsd:nonNegativeInteger` | `FunctionalProperty` | Valor numérico del rango (2 para Dos, 14 para As). |


---

## Decisiones de diseño

### Open World Assumption y clases cerradas

OWL opera bajo la **Suposición de Mundo Abierto (OWA)**: lo que no está afirmado es desconocido, no necesariamente falso. Esto implica que, sin medidas adicionales, un razonador admitiría la existencia de un quinto palo o de un decimocuarto rango (aunque este no exista).

Para cerrar el dominio se aplican dos mecanismos:

**`owl:oneOf`** en `Palo` y `Rango`: establece que los únicos individuos posibles son exactamente los declarados.

```
Palo  ≡ { Picas, Corazones, Diamantes, Tréboles }   (4 palos)
Rango ≡ { Dos, Tres, ..., Rey, As }                  (13 rangos)
```

**`owl:AllDifferent`** en los 69 individuos (3 bloques: palos, rangos y cartas): garantiza que el razonador los trate como entidades distintas, simulando la Unique Name Assumption (UNA) que OWL no asume por defecto.

### Propiedad *shortcut* `manoTienePar`

El clasificador `DoblePar` requiere detectar que una mano contiene dos pares de rangos **distintos**. En OWL 2 DL no es posible expresar directamente "dos rangos distintos, cada uno con al menos 2 cartas" usando solo `contieneCarta` y cardinalidades calificadas, porque OWL 2 DL tiene una limitación de cardinalidades calificadas cuando el cuantificador se aplica sobre individuos de la misma clase. No puede identificar que hay cosas distintas del mismo tipo de cosa.

La solución para construir un clasificador sin pasar por todas las combinaciones de manos `DoblePar`, es una **propiedad shortcut** `manoTienePar : Mano → Rango` que se agrega manualmente en el ABox para cada par presente en la mano. 

### Disjunción entre tipos de mano

Los tipos de mano son **conceptualmente disjuntos** en las reglas del póker (una mano no puede ser Par y Trío, aunque uno este contenido en el otro). Sin embargo, la ontología **no declara axiomas `owl:disjointWith`** entre ellos de forma explícita.

Esta decisión es deliberada: la definición con `owl:equivalentClass` ya expresa con precisión qué es cada mano, y añadir disjunción explícita introduce una complejidad que puede y debe ser realizada como trabajo futuro a partir del trabajo logrado en esta memoria, pero que dificulta la verificación del razonador en costos temporales y computacionales. Las intersecciones necesarias para `Full` y `EscaleraColor` son inferencialmente consistentes bajo esta configuración.

---