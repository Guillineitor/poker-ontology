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
  - Si el último rango tiene un valor bajo alternativo (como el As en la
    baraja inglesa, que vale 1 en la escalera baja)

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


def seccion_abox_rangos(rangos: list[str], rango_bajo: str | None) -> str:
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
        # Si este es el último rango y tiene valor bajo alternativo
        if rango_bajo and r == rangos[-1]:
            lines += [
                f'    deck:tieneValorRangoBajo "1"^^xsd:nonNegativeInteger ;',
            ]
        lines.append(f'    rdfs:label "{label(r)}" .')
        lines.append("")

    # Si hay valor bajo, declarar la propiedad
    if rango_bajo:
        ultimo_id = to_id(rangos[-1])
        extra = [
            "",
            "deck:tieneValorRangoBajo a owl:DatatypeProperty , owl:FunctionalProperty ;",
            "    rdfs:domain [",
            "        a owl:Class ;",
            f"        owl:oneOf ( deck:{ultimo_id} )",
            "    ] ;",
            "    rdfs:range xsd:nonNegativeInteger ;",
            '    rdfs:label "Tiene Valor De Rango Bajo" ;',
            f'    rdfs:comment "Valor alternativo bajo de {label(rangos[-1])} (= 1) para escalera baja. Restringido exclusivamente a {label(rangos[-1])}." .',
        ]
        lines += extra

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
# Ensamblaje final
# =============================================================================

def generar_ontologia(
    deck_name: str,
    base_iri: str,
    palos: list[str],
    rangos: list[str],
    rango_bajo: bool,
) -> str:
    partes = [
        header(base_iri, deck_name, len(palos), len(rangos)),
        seccion_palo(palos),
        seccion_rango(rangos),
        seccion_carta(),
        subclases_por_palo(palos),
        subclases_por_rango(rangos),
        seccion_grupos(),
        seccion_propiedades(),
        seccion_abox_palos(palos),
        seccion_abox_rangos(rangos, rango_bajo=rangos[-1] if rango_bajo else None),
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
    resp = pedir(
        f"¿El último rango ({rangos[-1].strip()}) tiene valor bajo alternativo (como el As en la baraja inglesa)? (s/n)",
        "n"
    ).lower()
    rango_bajo = resp in ("s", "si", "sí", "y", "yes")

    print()
    print(f"  Palos  : {len(palos)}  → {', '.join(palos)}")
    print(f"  Rangos : {len(rangos)}  → {', '.join(rangos)}")
    print(f"  Cartas : {len(palos) * len(rangos)}")
    print(f"  Rango bajo alternativo: {'sí' if rango_bajo else 'no'}")
    print()

    ttl = generar_ontologia(deck_name, base_iri, palos, rangos, rango_bajo)

    output_path = Path(f"{slug}.ttl")
    output_path.write_text(ttl, encoding="utf-8")
    print(f"✓ Ontología generada: {output_path.resolve()}")


if __name__ == "__main__":
    main()
