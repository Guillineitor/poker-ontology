# Ontología de Póker Texas Hold'em

Ontología escrita en OWL 2 DL que modela elementos del dominio del juego Póker Texas Hold'em: la baraja de 52 cartas y los diez tipos de mano estándar del póker, definidos como clases con clasificación automática para inferencia de los razonadores OWL. Está serializada en sintaxis Turtle (`.ttl`).

Otros aspectos del juego como apuestas, rondas y posiciones no forman parte del alcance y objetivos de esta ontología.

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
- Propiedades de Objeto
- Decisiones de diseño
  - Open World Assumption y clases cerradas
  - Propiedad shortcut manoTienePar
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

---

## Perfil OWL y razonadores compatibles

La ontología usa construcciones de OWL 2 DL: cardinalidades calificadas, valores nominales (owl:hasValue), enumeraciones (owl:oneOf) y restricciones universales (owl:allValuesFrom)."

Razonadores disponibles en la OWL API para la benchmark:

| Razonador | Versión mínima recomendada | Notas |
|---|---|---|
| **HermiT** | 1.4.x | Integrado en Protégé |
| **Openllet** | 2.6.x | Fork activo de Pellet|
| **JFact** | 5.x | Port Java de FaCT++ |

ELK no es compatible porque solo soporta OWL 2 EL y no admite cardinalidades calificadas.

---

## Estructura de la ontología

### TBox: clases y propiedades

La TBox define el esquema conceptual del dominio:

- `Palo` y `Rango` como enumeraciones cerradas.
- `Carta` con 17 subclases: 4 por palo y 13 por rango.
- `Mano` con 9 subclases de tipo de mano, cada una con su `owl:equivalentClass`.
- 4 propiedades de objeto.

### ABox: individuos

La ABox declara los 69 individuos concretos del dominio:

| Tipo | Cantidad | Descripción |
|---|---|---|
| `Palo` | 4 | Picas, Corazones, Diamantes, Tréboles |
| `Rango` | 13 | Dos (2) a As (14) |
| `Carta` | 52 | 13 rangos × 4 palos |

Los 69 individuos están declarados en tres bloques `owl:AllDifferent` separados (palos, rangos y cartas), para simular la Unique Name Assumption que OWL no aplica por defecto.

---

## Clases

### Carta y sus subclases

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

Las subclases por palo se usan en los clasificadores de `Color` y `EscaleraColor`. Las subclases por rango se usan en los clasificadores de `Par`, `Trio`, `Escalera`, `Poker` y `EscaleraReal`.

### Mano y tipos de mano

Una `Mano` contiene exactamente 5 cartas, expresado con cardinalidades mínima y máxima calificadas sobre `contieneCarta`.

Los tipos de mano se ordenan de menor a mayor fortaleza:

| # | Clase OWL | Nombre | Definición OWL resumida |
|---|---|---|---|
| 1 | `CartaAlta` | Carta Alta | `Mano ⊓ ∃contieneCarta.Carta` |
| 2 | `Par` | Par | `Mano ⊓ (≥2 CartaDeDos ⊔ … ⊔ ≥2 CartaDeAs)` |
| 3 | `DoblePar` | Doble Par | `Mano ⊓ ≥2 manoTienePar` |
| 4 | `Trio` | Trío | `Mano ⊓ (≥3 CartaDeDos ⊔ … ⊔ ≥3 CartaDeAs)` |
| 5 | `Escalera` | Escalera | `Mano ⊓ (A-2-3-4-5 ⊔ … ⊔ 10-J-Q-K-A)` |
| 6 | `Color` | Color | `Mano ⊓ (∀contieneCarta.CartaDeCorazones ⊔ … ⊔ ∀contieneCarta.CartaDeTreboles)` |
| 7 | `Full` | Full | `Trio ⊓ DoblePar` |
| 8 | `Poker` | Póker | `Mano ⊓ (≥4 CartaDeDos ⊔ … ⊔ ≥4 CartaDeAs)` |
| 9 | `EscaleraColor` | Escalera de Color | `Escalera ⊓ Color` |
| 10 | `EscaleraReal` | Escalera Real | `EscaleraColor ⊓ ∃contieneCarta.CartaDeDiez ⊓ … ⊓ ∃contieneCarta.CartaDeAs` |

`Full` y `EscaleraColor` se definen como intersecciones de clases ya existentes, lo que es conceptualmente exacto y evita redefinir condiciones más complejas de lo necesario en esta ontología. `EscaleraReal` es subclase de `EscaleraColor`, no un tipo independiente; es el único caso particular de escalera de color que tiene nombre propio en las reglas del póker.

---

## Propiedades de Objeto

| Propiedad | Dominio | Rango | Tipo | Descripción |
|---|---|---|---|---|
| `tienePalo` | `Carta` | `Palo` | `FunctionalProperty` | Asocia cada carta con su único palo. |
| `tieneRango` | `Carta` | `Rango` | `FunctionalProperty` | Asocia cada carta con su único rango. |
| `contieneCarta` | `Mano` | `Carta` | — | Relaciona una mano con las 5 cartas que la componen. |
| `manoTienePar` | `Mano` | `Rango` | — | Shortcut: indica qué rangos tienen al menos 2 cartas en la mano. Se agrega manualmente en la ABox. Usada por `DoblePar`. |

---

## Decisiones de diseño

### Open World Assumption y clases cerradas

OWL opera bajo la **Suposición de Mundo Abierto (OWA)**: lo que no está afirmado es desconocido, no necesariamente falso. Sin medidas adicionales, un razonador admitiría la existencia de un quinto palo o un decimocuarto rango que simplemente no se ha definido aún.

Para cerrar el dominio se aplican dos mecanismos:

**`owl:oneOf`** en `Palo` y `Rango` fija exactamente qué individuos pertenecen a cada clase:

```
Palo  ≡ { Picas, Corazones, Diamantes, Tréboles }   (4 palos)
Rango ≡ { Dos, Tres, ..., Rey, As }                  (13 rangos)
```

**`owl:AllDifferent`** en los 69 individuos (3 bloques: palos, rangos y cartas) garantiza que el razonador los trate como entidades distintas, simulando la Unique Name Assumption (UNA) que OWL no asume por defecto.

### Propiedad shortcut `manoTienePar`

El clasificador `DoblePar` requiere detectar que una mano contiene dos pares de rangos **distintos**. En OWL 2 DL no es posible expresar esto directamente con `contieneCarta` y cardinalidades calificadas, porque OWL 2 DL no puede identificar que hay dos cosas distintas del mismo tipo de cosa.

La solución es una **propiedad shortcut** `manoTienePar : Mano → Rango` que se agrega manualmente en la ABox para cada par presente en la mano. El clasificador entonces solo verifica que esa propiedad aparezca al menos dos veces, lo que sí es expresable con una cardinalidad simple.

### Disjunción entre tipos de mano

Los tipos de mano son conceptualmente disjuntos en las reglas del póker. Sin embargo, la ontología no declara axiomas `owl:disjointWith` entre ellos de forma explícita.

Esta decisión de diseño es a propósito, pues la definición con `owl:equivalentClass` ya expresa con precisión qué constituye cada mano, y añadir disjunción explícita introduce una complejidad computacional significativa en el razonador OWL cuando se procesa una ontología muy compleja. Declarar las manos como clases disjuntas queda como trabajo futuro a partir de lo logrado en esta versión de la ontología.
