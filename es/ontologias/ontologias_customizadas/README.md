# Ontologías Customizadas de Baraja

Ontologías generadas automáticamente por `generador_ontologias.py`, escritas en OWL 2 DL y serializadas en sintaxis Turtle (`.ttl`). Cada archivo modela una baraja genérica parametrizada por número de palos y número de rangos, manteniendo la misma arquitectura conceptual que la ontología base de póker.

---

## Contenido

- Descripción general
- Cómo se generan
- Catálogo de ontologías
  - Series por número de rangos
  - Tabla resumen
- Estructura común
  - TBox: clases y propiedades
  - ABox: individuos
- Clases
  - Palo y Rango
  - Carta y sus subclases
  - Mano y tipos de mano
- Propiedades
  - Propiedades de Objeto
  - Propiedades de Datos
- Decisiones de diseño
  - Nombres de palos y rangos
  - Escalera con pocos rangos
  - Rangos numéricos para barajas grandes

---

## Descripción general

| Atributo | Valor |
|---|---|
| Generador | `generador_ontologias.py` |
| Prefijo | `deck:` |
| Versión | `1.0.0` |
| Perfil OWL | OWL 2 DL |
| Serialización | Turtle (`.ttl`) |
| Idioma | Español |

Cada ontología modela una baraja con **P palos × R rangos = P·R cartas**, organizadas con la misma jerarquía de clases que la ontología base: palos y rangos cerrados por `owl:oneOf`, subclases de carta por palo y por rango, clase `Mano` con exactamente 5 cartas, y hasta 10 clasificadores de tipo de mano cuando el número de rangos lo permite.

---

## Cómo se generan

Las ontologías se producen ejecutando el generador desde la carpeta /generador_ontologias :

```bash
python generador_ontologias.py
```

El script solicita interactivamente:

1. **Nombre de la baraja** — usado como etiqueta y para construir el nombre del archivo `.ttl`.
2. **IRI base** — por defecto `http://www.ontologia-baraja.org/<nombre>`.
3. **Palos** — lista separada por comas, en el orden preferido.
4. **Rangos** — lista separada por comas, **de menor a mayor valor** (el orden determina las ventanas de `Escalera`).

El archivo resultante se guarda en `ontologias/ontologias_customizadas/<nombre>.ttl`.

---

## Catálogo de ontologías

Las ontologías están organizadas por número de rangos (7, 13, 19, 25, 31, 37) cruzado con número de palos (2, 4, 8, 12, 16). Los nombres de palos son customizados y usados son los siguientes según cantidad:

| Palos | Nombres |
|---|---|
| 2 | Fuego, Agua |
| 4 | Fuego, Agua, Planta, Eléctrico |
| 8 | Fuego, Agua, Planta, Eléctrico, Normal, Volador, Bicho, Veneno |
| 12 | Fuego, Agua, Planta, Eléctrico, Normal, Volador, Bicho, Veneno, Tierra, Roca, Lucha, Psíquico |
| 16 | Fuego, Agua, Planta, Eléctrico, Normal, Volador, Bicho, Veneno, Tierra, Roca, Lucha, Psíquico, Fantasma, Hielo, Dragón, Siniestro |

### Series por número de rangos

#### 7 rangos — `Uno` a `Siete`

| Archivo | Palos | Rangos | Cartas |
|---|---|---|---|
| `baraja_7r_2p.ttl` | 2 | 7 | 14 |
| `baraja_7r_4p.ttl` | 4 | 7 | 28 |
| `baraja_7r_8p.ttl` | 8 | 7 | 56 |
| `baraja_7r_12p.ttl` | 12 | 7 | 84 |
| `baraja_7r_16p.ttl` | 16 | 7 | 112 |

#### 13 rangos — `Uno` a `Trece`

| Archivo | Palos | Rangos | Cartas |
|---|---|---|---|
| `baraja_13r_2p.ttl` | 2 | 13 | 26 |
| `baraja_13r_4p.ttl` | 4 | 13 | 52 |
| `baraja_13r_8p.ttl` | 8 | 13 | 104 |
| `baraja_13r_12p.ttl` | 12 | 13 | 156 |
| `baraja_13r_16p.ttl` | 16 | 13 | 208 |

#### 19 rangos — `Uno` a `Diecinueve`

| Archivo | Palos | Rangos | Cartas |
|---|---|---|---|
| `baraja_19r_2p.ttl` | 2 | 19 | 38 |
| `baraja_19r_4p.ttl` | 4 | 19 | 76 |
| `baraja_19r_8p.ttl` | 8 | 19 | 152 |
| `baraja_19r_12p.ttl` | 12 | 19 | 228 |
| `baraja_19r_16p.ttl` | 16 | 19 | 304 |

#### 25 rangos — `Uno` a `Veinticinco`

| Archivo | Palos | Rangos | Cartas |
|---|---|---|---|
| `baraja_25r_2p.ttl` | 2 | 25 | 50 |
| `baraja_25r_4p.ttl` | 4 | 25 | 100 |
| `baraja_25r_8p.ttl` | 8 | 25 | 200 |
| `baraja_25r_12p.ttl` | 12 | 25 | 300 |
| `baraja_25r_16p.ttl` | 16 | 25 | 400 |

#### 31 rangos — `Uno` a `Treinta y uno`

| Archivo | Palos | Rangos | Cartas |
|---|---|---|---|
| `baraja_31r_2p.ttl` | 2 | 31 | 62 |
| `baraja_31r_4p.ttl` | 4 | 31 | 124 |
| `baraja_31r_8p.ttl` | 8 | 31 | 248 |
| `baraja_31r_12p.ttl` | 12 | 31 | 372 |
| `baraja_31r_16p.ttl` | 16 | 31 | 496 |

#### 37 rangos — `Uno` a `Treinta y siete`

| Archivo | Palos | Rangos | Cartas |
|---|---|---|---|
| `baraja_37r_2p.ttl` | 2 | 37 | 74 |
| `baraja_37r_4p.ttl` | 4 | 37 | 148 |
| `baraja_37r_8p.ttl` | 8 | 37 | 296 |
| `baraja_37r_12p.ttl` | 12 | 37 | 444 |
| `baraja_37r_16p.ttl` | 16 | 37 | 592 |

### Tabla resumen

| Rangos \ Palos | 2 | 4 | 8 | 12 | 16 |
|---|---|---|---|---|---|
| **7** | 14 | 28 | 56 | 84 | 112 |
| **13** | 26 | 52 | 104 | 156 | 208 |
| **19** | 38 | 76 | 152 | 228 | 304 |
| **25** | 50 | 100 | 200 | 300 | 400 |
| **31** | 62 | 124 | 248 | 372 | 496 |
| **37** | 74 | 148 | 296 | 444 | 592 |

*(Valores en número de cartas = palos × rangos)*

---

## Estructura común

Todas las ontologías del catálogo comparten la misma arquitectura. Solo varían los individuos ABox, los identificadores de subclases y los parámetros de cardinalidad derivados del número de palos y rangos.

### TBox: clases y propiedades

La TBox define el esquema conceptual del dominio. Incluye:

- Las clases `Palo` y `Rango` como enumeraciones cerradas con `owl:oneOf`.
- La clase `Carta` y sus subclases (P subclases por palo + R subclases por rango).
- La clase `Mano` con cardinalidades mínima y máxima de exactamente 5 cartas.
- Los clasificadores de tipo de mano como `owl:equivalentClass`.
- 4 propiedades de objeto y 1 propiedad de datos.

### ABox: individuos

La ABox declara todos los individuos concretos de la baraja:

| Tipo | Cantidad | Descripción |
|---|---|---|
| `Palo` | P | Un individuo por cada palo declarado |
| `Rango` | R | Un individuo por cada rango, con `tieneValorRango` ordinal |
| `Carta` | P × R | Una carta por cada combinación palo-rango |

Todos los individuos están declarados `owl:AllDifferent` en tres bloques separados (palos, rangos, cartas), simulando la Unique Name Assumption bajo OWA.

---

## Clases

### Palo y Rango

Ambas clases se cierran mediante `owl:equivalentClass [ owl:oneOf (...) ]`, enumerando exactamente los individuos declarados. Esto impide que el razonador asuma palos o rangos adicionales bajo la Open World Assumption.

```
Palo  ≡ { P₁, P₂, ..., Pₙ }   (n palos)
Rango ≡ { R₁, R₂, ..., Rₘ }   (m rangos, de menor a mayor valor)
```

### Carta y sus subclases

`Carta` se restringe a tener exactamente un palo (`tienePalo`, funcional) y exactamente un rango (`tieneRango`, funcional). Las subclases se generan en dos grupos:

**Por palo** — usadas por los clasificadores `Color` y `EscaleraColor`:

```
Carta
├── CartaDe<P₁>   ≡ tienePalo hasValue <P₁>
├── CartaDe<P₂>   ≡ tienePalo hasValue <P₂>
└── ...
```

**Por rango** — usadas por los clasificadores `Par`, `Trio`, `Escalera`, `Poker` y `EscaleraReal`:

```
Carta
├── CartaDe<R₁>   ≡ tieneRango hasValue <R₁>
├── CartaDe<R₂>   ≡ tieneRango hasValue <R₂>
└── ...
```

### Mano y tipos de mano

Una `Mano` contiene exactamente 5 cartas, expresado mediante cardinalidades mínima y máxima calificadas sobre `contieneCarta`.

Los tipos de mano se definen con `owl:equivalentClass` en orden de menor a mayor fortaleza. Los clasificadores `Escalera`, `EscaleraColor` y `EscaleraReal` solo se generan cuando **R ≥ 5**:

| # | Clase OWL | Nombre | Definición OWL resumida |
|---|---|---|---|
| 1 | `CartaAlta` | Carta Alta | `Mano ⊓ ∃contieneCarta.Carta` |
| 2 | `Par` | Par | `Mano ⊓ (≥2 CartaDe<R₁> ⊔ ... ⊔ ≥2 CartaDe<Rₘ>)` |
| 3 | `DoblePar` | Doble Par | `Mano ⊓ (≥2 manoTienePar)` |
| 4 | `Trio` | Trío | `Mano ⊓ (≥3 CartaDe<R₁> ⊔ ... ⊔ ≥3 CartaDe<Rₘ>)` |
| 5 | `Escalera` | Escalera | `Mano ⊓ (ventana R₁-R₅ ⊔ ... ⊔ ventana Rₘ₋₄-Rₘ)` — solo si R ≥ 5 |
| 6 | `Color` | Color | `Mano ⊓ (∀contieneCarta.CartaDe<P₁> ⊔ ... ⊔ ∀contieneCarta.CartaDe<Pₙ>)` |
| 7 | `Full` | Full | `Trio ⊓ DoblePar` |
| 8 | `Poker` | Póker | `Mano ⊓ (≥4 CartaDe<R₁> ⊔ ... ⊔ ≥4 CartaDe<Rₘ>)` |
| 9 | `EscaleraColor` | Escalera de Color | `Escalera ⊓ Color` — solo si R ≥ 5 |
| 10 | `EscaleraReal` | Escalera Real | `EscaleraColor ⊓ ∃contieneCarta.CartaDe<Rₘ₋₄> ⊓ ... ⊓ ∃contieneCarta.CartaDe<Rₘ>` — solo si R ≥ 5 |

`Full` y `EscaleraColor` se definen como intersecciones de clases ya existentes: `Full ≡ Trio ⊓ DoblePar` y `EscaleraColor ≡ Escalera ⊓ Color`. `EscaleraReal` fija los 5 rangos más altos de la lista de rangos declarada.

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
| `tieneValorRango` | `Rango` | `xsd:nonNegativeInteger` | `FunctionalProperty` | Valor ordinal del rango: 1 para el primero declarado, R para el último. Determina el orden de las ventanas de `Escalera`. |

---

## Decisiones de diseño

### Nombres de palos y rangos

Los nombres de palos y rangos son **etiquetas libres**: el generador los normaliza a identificadores CamelCase seguros para IRI (eliminando tildes, signos no alfanuméricos y espacios). El texto original se conserva en `rdfs:label` para mantener legibilidad en Protégé.

Por ejemplo, el palo `"Espadas"` produce el individuo `deck:Espadas` y la subclase `deck:CartaDeEspadas`.

### Escalera con pocos rangos

Cuando **R < 5**, no es posible definir ventanas de cinco rangos consecutivos. En ese caso el generador omite los clasificadores `Escalera`, `EscaleraColor` y `EscaleraReal`, e inserta un comentario explicativo en el archivo `.ttl`. Los demás clasificadores (`Par`, `DoblePar`, `Trio`, `Color`, `Full`, `Poker`) se generan siempre, independientemente del número de rangos.

Todas las ontologías de este catálogo tienen R ≥ 7, por lo que **todas incluyen los 10 clasificadores**.

---