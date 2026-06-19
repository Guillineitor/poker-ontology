"""
Generador interactivo de ontologías OWL 2 DL para barajas.

El script produce un archivo Turtle (.ttl) con la misma estructura conceptual
que la ontología base de póker: clases para palos, rangos, cartas y manos;
propiedades de objeto/datos; individuos ABox para cada palo, rango y carta.
La variación queda limitada a la baraja indicada por el usuario: palos, rangos,
IRI base, etiquetas e individuos generados.

Flujo principal:
    1. Leer nombre, IRI, palos y rangos desde consola.
    2. Normalizar nombres libres a identificadores OWL/Turtle seguros.
    3. Ensamblar secciones TBox, clasificadores de manos y ABox.
    4. Guardar la ontología en ontologias/ontologias_customizadas/.
"""

import re
import sys
from pathlib import Path


# =============================================================================
# Helpers de nombre
# =============================================================================

def to_id(name: str) -> str:
    """
    Convierte texto de usuario en un identificador CamelCase seguro para Turtle.

    Elimina tildes y signos no alfanuméricos para evitar IRIs inválidos.
    """
    import unicodedata

    name = unicodedata.normalize("NFD", name)
    name = "".join(c for c in name if unicodedata.category(c) != "Mn")
    name = re.sub(r"[^\w\s\-]", "", name, flags=re.UNICODE)
    parts = re.split(r"[\s\-_]+", name.strip())
    return "".join(p.capitalize() for p in parts if p)


def label(name: str) -> str:
    """Devuelve una etiqueta legible para `rdfs:label` sin alterar el contenido."""
    return name.strip().capitalize()


# =============================================================================
# Bloques de la ontología
# =============================================================================

def header(base_iri: str, deck_name: str, n_palos: int, n_rangos: int) -> str:
    """Construye prefijos, metadatos OWL y resumen de cardinalidades."""
    n_cartas = n_palos * n_rangos
    return f"""\
# =============================================================================
# Ontología de baraja: {deck_name}
# Generada automáticamente por generar_ontologia_baraja.py
# =============================================================================

@prefix deck: <{base_iri}#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

# =============================================================================
#
# Propósito
# ---------
# Ontología OWL 2 DL que modela la estructura de una baraja de tipo '{deck_name}'.
# Palos  : {n_palos}
# Rangos : {n_rangos}
# Cartas : {n_cartas}
#
# Open World Assumption (OWA)
# ---------------------------
# Palo, Rango y Carta se cierran con owl:oneOf para evitar que el razonador
# asuma palos, rangos o cartas adicionales no declaradas.
# Los {n_cartas} individuos de cartas se declaran AllDifferent.
# =============================================================================

<{base_iri}>
    rdf:type owl:Ontology ;
    rdfs:label "Ontología de baraja {deck_name}" ;
    rdfs:comment "Ontología OWL 2 DL que modela la baraja '{deck_name}' ({n_palos} palos × {n_rangos} rangos = {n_cartas} cartas)." ;
    owl:versionInfo "1.0.0" .
"""


def seccion_palo(palos: list[str]) -> str:
    """Declara `deck:Palo` como clase cerrada mediante `owl:oneOf`."""
    ids = " ".join(f"deck:{to_id(p)}" for p in palos)
    lines = [
        "",
        "# =============================================================================",
        "# Palos y Rangos de las Cartas",
        "# =============================================================================",
        "#",
        f"# Palo  ≡ {{ {', '.join(to_id(p) for p in palos)} }}  ({len(palos)} palos)",
        "#",
        "",
        "# Definición de la clase Palo.",
        "deck:Palo a owl:Class ;",
        "    owl:equivalentClass [",
        "        a owl:Class ;",
        f"        owl:oneOf ( {ids} )",
        "    ] ;",
        '    rdfs:label "Palo" ;',
        f'    rdfs:comment "Palo de una carta. Clase cerrada: exactamente {", ".join(to_id(p) for p in palos)}." .',
    ]
    return "\n".join(lines)


def seccion_rango(rangos: list[str]) -> str:
    """Declara `deck:Rango` como clase cerrada en el orden recibido."""
    ids = " ".join(f"deck:{to_id(r)}" for r in rangos)
    lines = [
        "",
        "# Definición de la clase Rango.",
        "deck:Rango a owl:Class ;",
        "    owl:equivalentClass [",
        "        a owl:Class ;",
        f"        owl:oneOf ( {ids} )",
        "    ] ;",
        '    rdfs:label "Rango" ;',
        f'    rdfs:comment "Rango de una carta. Clase cerrada: exactamente {", ".join(to_id(r) for r in rangos)}." .',
    ]
    return "\n".join(lines)


def seccion_carta(palos: list[str], rangos: list[str]) -> str:
    """Define `deck:Carta` como clase cerrada y con palo/rango obligatorios."""
    carta_lines = []
    for p in palos:
        pid = to_id(p)
        grupo = [f"deck:{to_id(r)}De{pid}" for r in rangos]
        carta_lines.append("            " + " ".join(grupo))
    cartas_block = "\n".join(carta_lines)

    return f"""
# Definición de la clase Carta.
deck:Carta a owl:Class ;
    owl:equivalentClass [
        a owl:Class ;
        owl:oneOf (
{cartas_block}
        )
    ] ;
    rdfs:subClassOf [
        a owl:Restriction ;
        owl:onProperty deck:tienePalo ;
        owl:someValuesFrom deck:Palo
    ] ;
    rdfs:subClassOf [
        a owl:Restriction ;
        owl:onProperty deck:tieneRango ;
        owl:someValuesFrom deck:Rango
    ] ;
    rdfs:label "Carta" ;
    rdfs:comment "Una carta de la baraja." ."""


def subclases_por_palo(palos: list[str]) -> str:
    """Genera clases `CartaDe<Palo>` equivalentes a `tienePalo value <Palo>`."""
    lines = [
        "",
        "# Subclases de Carta por Palo.",
    ]
    for p in palos:
        pid = to_id(p)
        lines += [
            "",
            f"deck:CartaDe{pid} a owl:Class ;",
            "    rdfs:subClassOf deck:Carta ;",
            "    owl:equivalentClass [",
            "        a owl:Restriction ;",
            "        owl:onProperty deck:tienePalo ;",
            f"        owl:hasValue deck:{pid}",
            "    ] ;",
            f'    rdfs:label "Carta de {label(p)}" ;',
            f'    rdfs:comment "Una carta del palo de {label(p)}." .',
        ]
    return "\n".join(lines)


def subclases_por_rango(rangos: list[str]) -> str:
    """Genera clases `CartaDe<Rango>` equivalentes a `tieneRango value <Rango>`."""
    lines = [
        "",
        "# Subclases de Carta por Rango.",
    ]
    for r in rangos:
        rid = to_id(r)
        lines += [
            "",
            f"deck:CartaDe{rid} a owl:Class ;",
            "    rdfs:subClassOf deck:Carta ;",
            f"    owl:equivalentClass [ a owl:Restriction ; owl:onProperty deck:tieneRango ; owl:hasValue deck:{rid} ] ;",
            f'    rdfs:label "Carta de {label(r)}" .',
        ]
    return "\n".join(lines)


def seccion_grupos() -> str:
    """Define `deck:Mano` como grupo de exactamente cinco cartas."""
    return """

# =============================================================================
# Grupos de Cartas
# =============================================================================

# Definición de la clase Mano.
deck:Mano a owl:Class ;
    rdfs:subClassOf [
        a owl:Restriction ;
        owl:onProperty deck:contieneCarta ;
        owl:maxQualifiedCardinality "5"^^xsd:nonNegativeInteger ;
        owl:onClass deck:Carta
    ] ;
    rdfs:subClassOf [
        a owl:Restriction ;
        owl:onProperty deck:contieneCarta ;
        owl:minQualifiedCardinality "5"^^xsd:nonNegativeInteger ;
        owl:onClass deck:Carta
    ] ;
    rdfs:label "Mano" ;
    rdfs:comment "La mejor combinación de 5 cartas de un jugador." ."""


def seccion_propiedades() -> str:
    """Declara propiedades de objeto y datos usadas por cartas, manos y rangos."""
    return """

# =============================================================================
# Propiedades de Objeto
# =============================================================================

deck:tienePalo a owl:ObjectProperty , owl:FunctionalProperty ;
    rdfs:domain deck:Carta ;
    rdfs:range deck:Palo ;
    rdfs:label "Tiene Palo" ;
    rdfs:comment "Asocia una carta con su palo. Funcional: cada carta tiene exactamente un palo." .

deck:tieneRango a owl:ObjectProperty , owl:FunctionalProperty ;
    rdfs:domain deck:Carta ;
    rdfs:range deck:Rango ;
    rdfs:label "Tiene Rango" ;
    rdfs:comment "Asocia una carta con su rango. Funcional: cada carta tiene exactamente un rango." .

deck:contieneCarta a owl:ObjectProperty ;
    rdfs:domain deck:Mano ;
    rdfs:range deck:Carta ;
    rdfs:label "Contiene Carta" ;
    rdfs:comment "Relaciona una mano con cada una de las cartas que la componen." .

deck:manoTienePar a owl:ObjectProperty ;
    rdfs:domain deck:Mano ;
    rdfs:range  deck:Rango ;
    rdfs:label  "Mano tiene Par" ;
    rdfs:comment "Atajo que indica qué rangos están presentes con al menos 2 cartas en la mano. Se agrega manualmente en el ABox. Usado por el clasificador de DoblePar." .

# =============================================================================
# Propiedades de Datos
# =============================================================================

deck:tieneValorRango a owl:DatatypeProperty , owl:FunctionalProperty ;
    rdfs:domain deck:Rango ;
    rdfs:range xsd:nonNegativeInteger ;
    rdfs:label "Tiene Valor De Rango" ;
    rdfs:comment "Valor numérico del rango. Usado por evaluadores externos." ."""


def seccion_abox_palos(palos: list[str]) -> str:
    """Crea los individuos ABox para cada palo de la baraja."""
    lines = [
        "",
        "# =============================================================================",
        "# Instancias (ABox)",
        "# =============================================================================",
        "",
        f"# Palos ({len(palos)} individuos) " + "-" * 43,
        "",
    ]
    for p in palos:
        pid = to_id(p)
        lines += [
            f"deck:{pid} a deck:Palo ;",
            f'    rdfs:label "{label(p)}" .',
        ]
    return "\n".join(lines)


def seccion_abox_rangos(rangos: list[str]) -> str:
    """Crea rangos con valor ordinal, usando la posición de la lista como fuerza."""
    lines = [
        "",
        f"# Rangos ({len(rangos)} individuos) " + "-" * 43,
        f"# Los valores van de 1 (primer rango) a {len(rangos)} (último rango).",
        "",
    ]
    for i, r in enumerate(rangos, start=1):
        rid = to_id(r)
        lines += [
            f"deck:{rid} a deck:Rango ;",
            f'    deck:tieneValorRango "{i}"^^xsd:nonNegativeInteger ;',
        ]
        lines.append(f'    rdfs:label "{label(r)}" .')
        lines.append("")

    return "\n".join(lines)


def seccion_abox_cartas(palos: list[str], rangos: list[str]) -> str:
    """Crea una carta por cada combinación palo-rango."""
    n = len(palos) * len(rangos)
    lines = [
        "",
        f"# Cartas ({n} individuos) " + "-" * 43,
        "",
    ]
    for p in palos:
        pid = to_id(p)
        lines.append(f"# Cartas de {label(p)}.")
        lines.append("")
        for r in rangos:
            rid = to_id(r)
            carta_id = f"{rid}De{pid}"
            lines += [
                f"deck:{carta_id} a deck:Carta ;",
                f"    deck:tienePalo deck:{pid} ; deck:tieneRango deck:{rid} ;",
                f'    rdfs:label "{label(r)} de {label(p)}" .',
            ]
        lines.append("")

    return "\n".join(lines)


def seccion_all_different(palos: list[str], rangos: list[str]) -> str:
    """Declara palos, rangos y cartas como individuos mutuamente distintos."""
    ids_palos = " ".join(f"deck:{to_id(p)}" for p in palos)
    ids_rangos = " ".join(f"deck:{to_id(r)}" for r in rangos)

    # Una línea por palo mantiene legible el bloque cuando hay muchas cartas.
    carta_lines = []
    for p in palos:
        pid = to_id(p)
        grupo = [f"deck:{to_id(r)}De{pid}" for r in rangos]
        carta_lines.append("        " + " ".join(grupo))

    cartas_block = "\n".join(carta_lines)

    n_palos  = len(palos)
    n_rangos = len(rangos)
    n_cartas = n_palos * n_rangos

    return f"""
# {n_palos} palos distintos
[] a owl:AllDifferent ;
    owl:distinctMembers ( {ids_palos} ) .

# {n_rangos} rangos distintos
[] a owl:AllDifferent ;
    owl:distinctMembers ( {ids_rangos} ) .

# {n_cartas} cartas distintas
[] a owl:AllDifferent ;
    owl:distinctMembers (
{cartas_block}
    ) .
"""


# =============================================================================
# Clasificadores de Manos
# =============================================================================

HAND_ORDER = [
    ("carta_alta", "CartaAlta", "Sin combinación; gana la carta más alta"),
    ("par", "Par", "Dos cartas del mismo rango"),
    ("doble_par", "DoblePar", "Dos pares distintos"),
    ("trio", "Trio", "Tres cartas del mismo rango"),
    ("escalera", "Escalera", "Cinco cartas consecutivas"),
    ("color", "Color", "Cinco cartas del mismo palo"),
    ("full", "Full", "Un trío más un par"),
    ("poker", "Poker", "Cuatro cartas del mismo rango"),
    ("escalera_color", "EscaleraColor", "Cinco cartas consecutivas del mismo palo"),
    ("escalera_real", "EscaleraReal", "Rangos más altos del mismo palo"),
]


def capacidades_manos(palos: list[str], rangos: list[str]) -> tuple[dict[str, bool], dict[str, str]]:
    """
    Calcula qué clasificadores tienen sentido para la baraja finita.

    Las reglas parten de una carta por combinación palo-rango y manos de cinco
    cartas. Por ejemplo, `Trio` requiere al menos tres palos porque no puede
    haber tres cartas del mismo rango con solo dos palos.
    """
    n_palos = len(palos)
    n_rangos = len(rangos)
    n_cartas = n_palos * n_rangos
    hay_mano = n_cartas >= 5

    posibles = {
        "carta_alta": hay_mano,
        "par": hay_mano and n_palos >= 2,
        "doble_par": hay_mano and n_palos >= 2 and n_rangos >= 2,
        "trio": hay_mano and n_palos >= 3,
        "escalera": hay_mano and n_rangos >= 5,
        "color": hay_mano and n_rangos >= 5,
        "full": hay_mano and n_palos >= 3 and n_rangos >= 2,
        "poker": hay_mano and n_palos >= 4,
        "escalera_color": hay_mano and n_rangos >= 5,
        "escalera_real": hay_mano and n_rangos >= 5,
    }

    motivos = {}
    if not hay_mano:
        base = "la baraja tiene menos de 5 cartas"
        return posibles, {key: base for key, enabled in posibles.items() if not enabled}

    if n_palos < 2:
        motivos["par"] = "requiere al menos 2 palos"
        motivos["doble_par"] = "requiere al menos 2 palos"
    if n_rangos < 2:
        motivos["doble_par"] = "requiere al menos 2 rangos"
        motivos["full"] = "requiere al menos 2 rangos"
    if n_palos < 3:
        motivos["trio"] = "requiere al menos 3 palos"
        motivos["full"] = "requiere al menos 3 palos"
    if n_palos < 4:
        motivos["poker"] = "requiere al menos 4 palos"
    if n_rangos < 5:
        motivos["escalera"] = "requiere al menos 5 rangos"
        motivos["color"] = "requiere al menos 5 rangos por palo"
        motivos["escalera_color"] = "requiere al menos 5 rangos"
        motivos["escalera_real"] = "requiere al menos 5 rangos"

    return posibles, {key: motivos[key] for key, enabled in posibles.items() if not enabled}


def seccion_clasificadores(posibles: dict[str, bool], motivos: dict[str, str]) -> str:
    """Genera el encabezado dinámico de clasificadores incluidos y omitidos."""
    lineas = [
        "",
        "# =============================================================================",
        "# Clasificadores de Manos",
        "# =============================================================================",
        "#",
        "# Jerarquía de tipos de mano generados para esta baraja:",
        "#   Mano",
    ]

    for index, (key, nombre, descripcion) in enumerate(HAND_ORDER, start=1):
        if posibles.get(key, False):
            lineas.append(f"#   ├── {nombre:<14} ({index}) {descripcion}")

    omitidas = [(nombre, motivos[key]) for key, nombre, _ in HAND_ORDER if key in motivos]
    if omitidas:
        lineas += [
            "#",
            "# Tipos de mano no generados para esta baraja:",
        ]
        for nombre, motivo in omitidas:
            lineas.append(f"#   - {nombre}: {motivo}.")

    lineas.append("#")
    return "\n".join(lineas)


def clasificador_carta_alta() -> str:
    """Define CartaAlta como una mano con al menos una carta."""
    lineas = [
        "",
        "# Definición de la clase CartaAlta.",
        "deck:CartaAlta a owl:Class ;",
        "    owl:equivalentClass [",
        "        a owl:Class ;",
        "        owl:intersectionOf (",
        "            deck:Mano",
        "            [",
        "                a owl:Restriction ;",
        "                owl:onProperty deck:contieneCarta ;",
        "                owl:someValuesFrom deck:Carta",
        "            ]",
        "        )",
        "    ] ;",
        "    rdfs:subClassOf deck:Mano ;",
        '    rdfs:label "Carta Alta" ;',
        '    rdfs:comment "Mano formada sin combinación; la carta más alta decide el ganador." .',
    ]
    return "\n".join(lineas)


def clasificador_par(rangos: list[str]) -> str:
    """
    Define Par como unión de restricciones `minQualifiedCardinality 2`.

    Se debe llamar solo si la baraja tiene al menos dos palos.
    """
    lineas = [
        "",
        "# Definición de la clase Par.",
        "deck:Par a owl:Class ;",
        "    owl:equivalentClass [",
        "        a owl:Class ;",
        "        owl:intersectionOf (",
        "            deck:Mano",
        "            [",
        "                a owl:Class ;",
        "                owl:unionOf (",
    ]
    for r in rangos:
        rid = to_id(r)
        lineas.append(
            f'                    # Par de {label(r)} de cualquier palo.'
        )
        lineas.append(
            f'                    [ a owl:Restriction ; owl:onProperty deck:contieneCarta ; owl:minQualifiedCardinality "2"^^xsd:nonNegativeInteger ; owl:onClass deck:CartaDe{rid} ]'
        )
    lineas += [
        "                )",
        "            ]",
        "        )",
        "    ] ;",
        '    rdfs:label "Par" ;',
        '    rdfs:comment "Mano formada por dos cartas del mismo rango." .',
    ]
    return "\n".join(lineas)


def clasificador_doble_par(rangos: list[str]) -> str:
    """
    Define DoblePar a partir de la propiedad auxiliar `manoTienePar`.

    El ABox debe indicar qué rangos forman par en cada mano; el clasificador
    exige al menos dos valores distintos para esa propiedad.
    """
    lineas = [
        "",
        "# Definición de la clase DoblePar.",
        "# Usa el atajo manoTienePar: la mano tiene al menos 2 rangos con par.",
        "deck:DoblePar a owl:Class ;",
        "    owl:equivalentClass [",
        "        a owl:Class ;",
        "        owl:intersectionOf (",
        "            deck:Mano",
        "            [ a owl:Restriction ;",
        "              owl:onProperty deck:manoTienePar ;",
        '              owl:minCardinality "2"^^xsd:nonNegativeInteger ]',
        "        )",
        "    ] ;",
        '    rdfs:label "Doble Par" ;',
        '    rdfs:comment "Mano formada por dos pares de rangos distintos, independientemente del palo." .',
    ]
    return "\n".join(lineas)


def clasificador_trio(rangos: list[str]) -> str:
    """Define Trío como unión de restricciones de 3 cartas para cada rango."""
    lineas = [
        "",
        "# Definición de la clase Trio.",
        "deck:Trio a owl:Class ;",
        "    owl:equivalentClass [",
        "        a owl:Class ;",
        "        owl:intersectionOf (",
        "            deck:Mano",
        "            [",
        "                a owl:Class ;",
        "                owl:unionOf (",
    ]
    for r in rangos:
        rid = to_id(r)
        lineas.append(f'                    # Trío de {label(r)} de cualquier palo.')
        lineas.append(
            f'                    [ a owl:Restriction ; owl:onProperty deck:contieneCarta ; owl:minQualifiedCardinality "3"^^xsd:nonNegativeInteger ; owl:onClass deck:CartaDe{rid} ]'
        )
    lineas += [
        "                )",
        "            ]",
        "        )",
        "    ] ;",
        '    rdfs:label "Trío" ;',
        '    rdfs:comment "Mano formada por tres cartas del mismo rango." .',
    ]
    return "\n".join(lineas)


def clasificador_escalera(rangos: list[str]) -> str:
    """
    Define Escalera como unión de ventanas consecutivas de cinco rangos.

    Requiere que `rangos` venga ordenado de menor a mayor valor, porque cada
    ventana se toma directamente desde esa lista.
    """
    n = len(rangos)
    secuencias = []

    for i in range(n - 4):
        secuencias.append(rangos[i:i+5])

    def bloque_secuencia(seq: list[str]) -> str:
        """Serializa una ventana de cinco rangos como intersección OWL."""
        nombre = "-".join(label(r) for r in seq)
        restricciones = "\n".join(
            f'                        [ a owl:Restriction ; owl:onProperty deck:contieneCarta ; owl:someValuesFrom deck:CartaDe{to_id(r)} ]'
            for r in seq
        )
        return (
            f'                    # Escalera {nombre}.\n'
            f'                    [ a owl:Class ; owl:intersectionOf (\n'
            f'{restricciones}\n'
            f'                    )]'
        )

    lineas = [
        "",
        "# Definición de la clase Escalera.",
        "deck:Escalera a owl:Class ;",
        "    owl:equivalentClass [",
        "        a owl:Class ;",
        "        owl:intersectionOf (",
        "            deck:Mano",
        "            [",
        "                a owl:Class ;",
        "                owl:unionOf (",
    ]
    for seq in secuencias:
        lineas.append(bloque_secuencia(seq))
    lineas += [
        "                )",
        "            ]",
        "        )",
        "    ] ;",
        '    rdfs:label "Escalera" ;',
        '    rdfs:comment "Mano formada por cinco cartas de rangos consecutivos, no necesariamente del mismo palo." .',
    ]
    return "\n".join(lineas)


def clasificador_color(palos: list[str]) -> str:
    """Define Color como unión de restricciones `allValuesFrom` por palo."""
    lineas = [
        "",
        "# Definición de la clase Color.",
        "deck:Color a owl:Class ;",
        "    owl:equivalentClass [",
        "        a owl:Class ;",
        "        owl:intersectionOf (",
        "            deck:Mano",
        "            [",
        "                a owl:Class ;",
        "                owl:unionOf (",
    ]
    for p in palos:
        pid = to_id(p)
        lineas.append(f'                    # Color de {label(p)}.')
        lineas.append(
            f'                    [ a owl:Restriction ; owl:onProperty deck:contieneCarta ; owl:allValuesFrom deck:CartaDe{pid} ]'
        )
    lineas += [
        "                )",
        "            ]",
        "        )",
        "    ] ;",
        '    rdfs:label "Color" ;',
        '    rdfs:comment "Mano formada por cinco cartas del mismo palo, no necesariamente consecutivas." .',
    ]
    return "\n".join(lineas)


def clasificador_full() -> str:
    """
    Define Full como intersección de Trío y DoblePar.

    Reutilizar clases evita duplicar restricciones y mantiene el patrón de la
    ontología base.
    """
    return """
# Definición de la clase Full.
# Observación: El Full es la intersección de Trio y DoblePar.
deck:Full a owl:Class ;
    owl:equivalentClass [
        a owl:Class ;
        owl:intersectionOf (
            deck:Trio
            deck:DoblePar
        )
    ] ;
    rdfs:label "Full" ;
    rdfs:comment "Mano formada por tres cartas del mismo rango y dos cartas de otro mismo rango." ."""


def clasificador_poker_mano(rangos: list[str]) -> str:
    """Define Póker como unión de restricciones de 4 cartas para cada rango."""
    lineas = [
        "",
        "# Definición de la clase Poker.",
        "deck:Poker a owl:Class ;",
        "    owl:equivalentClass [",
        "        a owl:Class ;",
        "        owl:intersectionOf (",
        "            deck:Mano",
        "            [",
        "                a owl:Class ;",
        "                owl:unionOf (",
    ]
    for r in rangos:
        rid = to_id(r)
        lineas.append(f'                    # Póker de {label(r)} de cualquier palo.')
        lineas.append(
            f'                    [ a owl:Restriction ; owl:onProperty deck:contieneCarta ; owl:minQualifiedCardinality "4"^^xsd:nonNegativeInteger ; owl:onClass deck:CartaDe{rid} ]'
        )
    lineas += [
        "                )",
        "            ]",
        "        )",
        "    ] ;",
        '    rdfs:label "Póker" ;',
        '    rdfs:comment "Mano formada por cuatro cartas del mismo rango y una carta cualquiera." .',
    ]
    return "\n".join(lineas)


def clasificador_escalera_color() -> str:
    """
    Define Escalera de Color como intersección de Escalera y Color.

    Este patrón evita enumerar todas las combinaciones de secuencia y palo.
    """
    return """
# Definición de la clase EscaleraColor.
# Truco: intersección de Escalera y Color → no hay que enumerar combinaciones de palo.
deck:EscaleraColor a owl:Class ;
    owl:equivalentClass [
        a owl:Class ;
        owl:intersectionOf (
            deck:Escalera
            deck:Color
        )
    ] ;
    rdfs:label "Escalera de Color" ;
    rdfs:comment "Mano formada por cinco cartas consecutivas del mismo palo." ."""


def clasificador_escalera_real(rangos: list[str]) -> str:
    """
    Define Escalera Real como EscaleraColor con los cinco rangos más altos.

    Asume que `rangos` está ordenado de menor a mayor valor; por eso toma los
    últimos cinco elementos de la lista.
    """
    top5 = rangos[-5:]
    restricciones = "\n".join(
        f'            [ a owl:Restriction ; owl:onProperty deck:contieneCarta ; owl:someValuesFrom deck:CartaDe{to_id(r)} ]'
        for r in top5
    )
    nombre_top5 = "-".join(label(r) for r in top5)
    return f"""
# Definición de la clase EscaleraReal.
# Subclase de EscaleraColor con los 5 rangos más altos ({nombre_top5}).
deck:EscaleraReal a owl:Class ;
    rdfs:subClassOf deck:EscaleraColor ;
    owl:equivalentClass [
        a owl:Class ;
        owl:intersectionOf (
            deck:EscaleraColor
{restricciones}
        )
    ] ;
    rdfs:label "Escalera Real" ;
    rdfs:comment "Mano formada por los cinco rangos más altos consecutivos ({nombre_top5}) del mismo palo." ."""




# =============================================================================
# Ensamblaje final
# =============================================================================

def generar_ontologia(
    deck_name: str,
    base_iri: str,
    palos: list[str],
    rangos: list[str],
) -> str:
    """
    Ensambla la ontología completa en Turtle.

    `palos` y `rangos` deben venir validados por el llamador. Los
    clasificadores de manos se incluyen solo cuando la cantidad de palos,
    rangos y cartas permite formar físicamente esa combinación.
    """
    posibles, motivos = capacidades_manos(palos, rangos)

    partes = [
        header(base_iri, deck_name, len(palos), len(rangos)),
        seccion_palo(palos),
        seccion_rango(rangos),
        seccion_carta(palos, rangos),
        subclases_por_palo(palos),
        subclases_por_rango(rangos),
        seccion_grupos(),
        seccion_clasificadores(posibles, motivos),
    ]

    if posibles["carta_alta"]:
        partes.append(clasificador_carta_alta())
    if posibles["par"]:
        partes.append(clasificador_par(rangos))
    if posibles["doble_par"]:
        partes.append(clasificador_doble_par(rangos))
    if posibles["trio"]:
        partes.append(clasificador_trio(rangos))
    if posibles["escalera"]:
        partes.append(clasificador_escalera(rangos))
    if posibles["color"]:
        partes.append(clasificador_color(palos))
    if posibles["full"]:
        partes.append(clasificador_full())
    if posibles["poker"]:
        partes.append(clasificador_poker_mano(rangos))
    if posibles["escalera_color"]:
        partes.append(clasificador_escalera_color())
    if posibles["escalera_real"]:
        partes.append(clasificador_escalera_real(rangos))

    partes += [
        seccion_propiedades(),
        seccion_abox_palos(palos),
        seccion_abox_rangos(rangos),
        seccion_abox_cartas(palos, rangos),
        seccion_all_different(palos, rangos),
    ]
    return "\n".join(partes)


# =============================================================================
# Interfaz interactiva
# =============================================================================

def pedir(prompt: str, default: str = "") -> str:
    """Lee una cadena desde consola y devuelve `default` si la entrada está vacía."""
    sufijo = f" [{default}]" if default else ""
    valor = input(f"{prompt}{sufijo}: ").strip()
    return valor if valor else default


def pedir_lista(prompt: str, ejemplo: str) -> list[str]:
    """Lee una lista separada por comas, limpiando espacios y elementos vacíos."""
    print(f"  (ejemplo: {ejemplo})")
    raw = input(f"{prompt}: ").strip()
    items = [x.strip() for x in raw.split(",") if x.strip()]
    return items


def main() -> None:
    """Ejecuta la interfaz interactiva y escribe el archivo Turtle resultante."""
    print("=" * 60)
    print("  Generador de Ontología de Baraja (OWL 2 DL / Turtle)")
    print("=" * 60)
    print()

    deck_name = pedir("Nombre de la baraja", "MiBaraja")
    slug = re.sub(r"\s+", "_", deck_name.lower())
    base_iri = pedir(
        "IRI base de la ontología",
        f"http://www.ontologia-baraja.org/{slug}"
    )

    print()
    palos = pedir_lista(
        "Palos (separados por coma, en el orden que prefieras)",
        "Copas, Oros, Espadas, Bastos"
    )
    if len(palos) < 1:
        print("Error: debes definir al menos 1 palo.")
        sys.exit(1)

    print()
    rangos = pedir_lista(
        "Rangos (separados por coma, de menor a mayor valor)",
        "As, Dos, Tres, Cuatro, Cinco, Seis, Siete, Sota, Caballo, Rey"
    )
    if len(rangos) < 1:
        print("Error: debes definir al menos 1 rango.")
        sys.exit(1)

    print()
    print(f"  Palos  : {len(palos)}  → {', '.join(palos)}")
    print(f"  Rangos : {len(rangos)}  → {', '.join(rangos)}")
    print(f"  Cartas : {len(palos) * len(rangos)}")
    print()

    ttl = generar_ontologia(deck_name, base_iri, palos, rangos)

    output_dir = Path(__file__).parent.parent / "ontologias" / "ontologias_customizadas"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{slug}.ttl"
    output_path.write_text(ttl, encoding="utf-8")
    print(f"✓ Ontología generada: {output_path.resolve()}")

if __name__ == "__main__":
    main()
