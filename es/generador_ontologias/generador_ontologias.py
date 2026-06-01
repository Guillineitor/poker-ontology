"""
generar_ontologia_baraja.py
===========================
Genera una ontología OWL 2 DL en formato Turtle (.ttl) para cualquier tipo
de baraja, manteniendo la estructura idéntica a la ontología base de póker
(ontologia_base_poker.ttl). Solo cambian los palos, los rangos y los
individuos de cartas.

Uso
---
    python generar_ontologia_baraja.py

El script pedirá interactivamente:
  - Nombre de la baraja (usado en etiquetas y nombre de archivo)
  - IRI base de la ontología
  - Lista de palos  (separados por coma)
  - Lista de rangos (separados por coma, en orden ascendente de valor)

Salida
------
    <nombre_baraja>.ttl   en el directorio actual
"""

import re
import sys
from itertools import combinations
from pathlib import Path


# =============================================================================
# Helpers de nombre
# =============================================================================

def to_id(name: str) -> str:
    """
    Convierte un nombre libre en un identificador CamelCase válido para OWL.
    Ej: 'copas' -> 'Copas', 'Sota de Copas' -> 'SotaDeCopas'
    """
    # Elimina caracteres que no sean letras, dígitos ni espacios/guiones
    name = re.sub(r"[^\w\s\-]", "", name, flags=re.UNICODE)
    parts = re.split(r"[\s\-_]+", name.strip())
    return "".join(p.capitalize() for p in parts if p)


def label(name: str) -> str:
    """Capitaliza la primera letra para usar como rdfs:label."""
    return name.strip().capitalize()


# =============================================================================
# Bloques de la ontología
# =============================================================================

def header(base_iri: str, deck_name: str, n_palos: int, n_rangos: int) -> str:
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
# Palo y Rango se cierran con owl:oneOf para evitar que el razonador asuma
# palos o rangos adicionales no declarados.
# Los {n_cartas} individuos de cartas se declaran AllDifferent.
# =============================================================================

<{base_iri}>
    rdf:type owl:Ontology ;
    rdfs:label "Ontología de baraja {deck_name}" ;
    rdfs:comment "Ontología OWL 2 DL que modela la baraja '{deck_name}' ({n_palos} palos × {n_rangos} rangos = {n_cartas} cartas)." ;
    owl:versionInfo "1.0.0" .
"""


def seccion_palo(palos: list[str]) -> str:
    ids = " ".join(f"deck:{to_id(p)}" for p in palos)
    rangos_enum = "\n#   " + "\n#   ".join(f"{to_id(p)}" for p in palos)
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


def seccion_carta() -> str:
    return """
# Definición de la clase Carta.
deck:Carta a owl:Class ;
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
            "    owl:equivalentClass [ a owl:Restriction ; owl:onProperty deck:tieneRango ; owl:hasValue deck:{rid} ] ;",
            f'    rdfs:label "Carta de {label(r)}" .',
        ]
    return "\n".join(lines)


def seccion_grupos() -> str:
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

# =============================================================================
# Propiedades de Datos
# =============================================================================

deck:tieneValorRango a owl:DatatypeProperty , owl:FunctionalProperty ;
    rdfs:domain deck:Rango ;
    rdfs:range xsd:nonNegativeInteger ;
    rdfs:label "Tiene Valor De Rango" ;
    rdfs:comment "Valor numérico del rango. Usado por evaluadores externos." ."""


def seccion_abox_palos(palos: list[str]) -> str:
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
    lines = [
        "",
        f"# Rangos ({len(rangos)} individuos) " + "-" * 43,
        "# Los valores van de 1 (primer rango) a {len(rangos)} (último rango).",
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
    # AllDifferent palos
    ids_palos = " ".join(f"deck:{to_id(p)}" for p in palos)

    # AllDifferent rangos
    ids_rangos = " ".join(f"deck:{to_id(r)}" for r in rangos)

    # AllDifferent cartas (en bloques de 10 por legibilidad)
    cartas = []
    for p in palos:
        pid = to_id(p)
        for r in rangos:
            rid = to_id(r)
            cartas.append(f"deck:{rid}De{pid}")

    # Formatear cartas en líneas de ~5 por palo
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

def clasificador_par(rangos: list[str]) -> str:
    """
    Par: al menos 2 cartas del mismo rango (cualquier rango).
    Patrón: owl:unionOf de minQualifiedCardinality 2 por cada rango.
    """
    lineas = [
        "",
        "# =============================================================================",
        "# Clasificadores de Manos",
        "# =============================================================================",
        "#",
        "# Jerarquía de tipos de mano, de menor a mayor fortaleza:",
        "#   Mano",
        "#   ├── CartaAlta      (1) Sin combinación; gana la carta más alta",
        "#   ├── Par            (2) Dos cartas del mismo rango",
        "#   ├── DoblePar       (3) Dos pares distintos",
        "#   ├── Trio           (4) Tres cartas del mismo rango",
        "#   ├── Escalera       (5) Cinco cartas consecutivas de distintos palos",
        "#   ├── Color          (6) Cinco cartas del mismo palo",
        "#   ├── FullHouse      (7) Un trío más un par",
        "#   ├── Poker          (8) Cuatro cartas del mismo rango",
        "#   └── EscaleraColor  (9) Cinco cartas consecutivas del mismo palo",
        "#         └── EscaleraReal  Escalera Real: rangos más altos del mismo palo",
        "#",
        "",
        "# Definición de la clase CartaAlta.",
        "deck:CartaAlta a owl:Class ;",
        "    rdfs:subClassOf deck:Mano ;",
        '    rdfs:label "Carta Alta" ;',
        '    rdfs:comment "Sin combinación; la carta más alta decide el ganador." .',
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
    Doble Par: dos pares de rangos distintos.
    Patrón: owl:unionOf de C(n,2) intersecciones, cada una con dos
    minQualifiedCardinality 2 sobre rangos distintos.
    """
    lineas = [
        "",
        "# Definición de la clase DoblePar.",
        "# Nota: En OWL DL puro es necesario enumerar las C(n,2) combinaciones de pares.",
        "deck:DoblePar a owl:Class ;",
        "    owl:equivalentClass [",
        "        a owl:Class ;",
        "        owl:intersectionOf (",
        "            deck:Mano",
        "            [",
        "                a owl:Class ;",
        "                owl:unionOf (",
    ]
    for r1, r2 in combinations(rangos, 2):
        r1id, r2id = to_id(r1), to_id(r2)
        lineas.append(
            f'                    # {label(r1)} + {label(r2)}, de cualquier palo.'
        )
        lineas.append(
            f'                    [ a owl:Class ; owl:intersectionOf ('
            f' [ a owl:Restriction ; owl:onProperty deck:contieneCarta ; owl:minQualifiedCardinality "2"^^xsd:nonNegativeInteger ; owl:onClass deck:CartaDe{r1id} ]'
            f' [ a owl:Restriction ; owl:onProperty deck:contieneCarta ; owl:minQualifiedCardinality "2"^^xsd:nonNegativeInteger ; owl:onClass deck:CartaDe{r2id} ]'
            f' ) ]'
        )
    lineas += [
        "                )",
        "            ]",
        "        )",
        "    ] ;",
        '    rdfs:label "Doble Par" ;',
        '    rdfs:comment "Dos pares de rangos distintos, independientemente del palo." .',
    ]
    return "\n".join(lineas)


def clasificador_trio(rangos: list[str]) -> str:
    """Trío: al menos 3 cartas del mismo rango."""
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
    Escalera: 5 cartas de rangos consecutivos, cualquier palo.
    Genera las (n-4) secuencias posibles de 5 rangos consecutivos.
    """
    n = len(rangos)
    secuencias = []

    # Secuencias normales consecutivas
    for i in range(n - 4):
        secuencias.append(rangos[i:i+5])

    def bloque_secuencia(seq):
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
    """Color: las 5 cartas del mismo palo (allValuesFrom por palo)."""
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


def clasificador_full_house(rangos: list[str]) -> str:
    """
    Full House: trío + par.
    Truco por exclusión aritmética: cada rango aporta 0, 2 ó 3 cartas
    (nunca 1, nunca 4). La única partición de 5 en {0,2,3} es 3+2.
    """
    lineas = [
        "",
        "# Definición de la clase FullHouse.",
        "# Truco por exclusión: cada rango tiene 0, 2 ó 3 cartas (nunca 1, nunca 4).",
        "# La única partición de 5 en {0,2,3} es 3+2 → Full House.",
        "deck:FullHouse a owl:Class ;",
        "    owl:equivalentClass [",
        "        a owl:Class ;",
        "        owl:intersectionOf (",
        "            deck:Mano",
    ]
    for r in rangos:
        rid = to_id(r)
        lineas += [
            f"            # 0, 2 ó 3 cartas de {label(r)}.",
            "            [ a owl:Class ; owl:intersectionOf (",
            f'                [ a owl:Restriction ; owl:onProperty deck:contieneCarta ; owl:maxQualifiedCardinality "3"^^xsd:nonNegativeInteger ; owl:onClass deck:CartaDe{rid} ]',
            "                [ a owl:Class ; owl:unionOf (",
            f'                    [ a owl:Restriction ; owl:onProperty deck:contieneCarta ; owl:maxQualifiedCardinality "0"^^xsd:nonNegativeInteger ; owl:onClass deck:CartaDe{rid} ]',
            f'                    [ a owl:Restriction ; owl:onProperty deck:contieneCarta ; owl:minQualifiedCardinality "2"^^xsd:nonNegativeInteger ; owl:onClass deck:CartaDe{rid} ]',
            "                )]",
            "            )]",
        ]
    lineas += [
        "        )",
        "    ] ;",
        '    rdfs:label "Full House" ;',
        '    rdfs:comment "Un trío más un par. Clasificado por exclusión: cada rango aporta 0, 2 ó 3 cartas; la única partición de 5 en {0,2,3} es 3+2." .',
    ]
    return "\n".join(lineas)


def clasificador_poker_mano(rangos: list[str]) -> str:
    """Póker: al menos 4 cartas del mismo rango."""
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
    Escalera de Color: intersección de Escalera y Color.
    El truco elegante: reutiliza las dos clases ya definidas,
    sin enumerar las (n-4) × p combinaciones explícitamente.
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
    Escalera Real: EscaleraColor con los 5 rangos más altos.
    Si hay rango bajo (As), los 5 más altos son los últimos 5 rangos
    (que siempre incluirán el As como rango alto).
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


def seccion_disjuncion_manos() -> str:
    """Declara las 9 clases de mano base como mutuamente disjuntas bajo Mano."""
    clases = [
        "deck:CartaAlta", "deck:Par", "deck:DoblePar", "deck:Trio",
        "deck:Escalera", "deck:Color", "deck:FullHouse", "deck:Poker",
        "deck:EscaleraColor",
    ]
    lista = " ".join(clases)
    return f"""
# Las 9 clases base de mano son mutuamente disjuntas entre sí.
[] a owl:AllDisjointClasses ;
    owl:members ( {lista} ) ."""


# =============================================================================
# Ensamblaje final
# =============================================================================

def generar_ontologia(
    deck_name: str,
    base_iri: str,
    palos: list[str],
    rangos: list[str],
) -> str:
    # Advertencia si hay menos de 5 rangos (no se pueden formar escaleras)
    tiene_escalera = len(rangos) >= 5

    partes = [
        header(base_iri, deck_name, len(palos), len(rangos)),
        seccion_palo(palos),
        seccion_rango(rangos),
        seccion_carta(),
        subclases_por_palo(palos),
        subclases_por_rango(rangos),
        seccion_grupos(),
        # Clasificadores de manos
        clasificador_par(rangos),
        clasificador_doble_par(rangos),
        clasificador_trio(rangos),
    ]

    if tiene_escalera:
        partes.append(clasificador_escalera(rangos))
    else:
        partes.append(
            "\n# NOTA: Con menos de 5 rangos no es posible definir Escalera.\n"
        )

    partes += [
        clasificador_color(palos),
        clasificador_full_house(rangos),
        clasificador_poker_mano(rangos),
    ]

    if tiene_escalera:
        partes.append(clasificador_escalera_color())
        partes.append(clasificador_escalera_real(rangos))
        partes.append(seccion_disjuncion_manos())

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
    sufijo = f" [{default}]" if default else ""
    valor = input(f"{prompt}{sufijo}: ").strip()
    return valor if valor else default


def pedir_lista(prompt: str, ejemplo: str) -> list[str]:
    print(f"  (ejemplo: {ejemplo})")
    raw = input(f"{prompt}: ").strip()
    items = [x.strip() for x in raw.split(",") if x.strip()]
    return items


def main():
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

    output_path = Path(f"{slug}.ttl")
    output_path.write_text(ttl, encoding="utf-8")
    print(f"✓ Ontología generada: {output_path.resolve()}")


if __name__ == "__main__":
    main()
