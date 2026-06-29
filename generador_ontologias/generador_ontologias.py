# =============================================================================
# generador_ontologias.py
# =============================================================================
# Generador de ontologías escritas en OWL 2 DL de Póker Texas Hold'em pero con barajas de cartas parametrizadas.
# 
# Este script produce una ontología en formato Turtle (.ttl) que sigue la misma estructura
# conceptual que la ontología base de póker: clases cerradas para palos, rangos
# y cartas; propiedades de objeto y datos; e individuos ABox para cada elemento
# de la baraja. La variación queda determinada por los parámetros que el usuario
# introduce en la consola: nombre de la baraja, palos y rangos.
#
# Uso:
#     python generador_ontologias.py
#
# Flujo principal:
#     1. Solicitar nombre, palos y rangos desde la consola.
#     2. Derivar la IRI base y el nombre del archivo de salida a partir del nombre.
#     3. Normalizar los nombres libres a identificadores OWL/Turtle seguros.
#     4. Calcular qué clasificadores de manos son válidos para la baraja indicada (dependiendo de la cantidad de palos y rangos).
#     5. Ensamblar las secciones TBox, clasificadores de manos y ABox.
#     6. Guardar la ontología en la carpeta ontologias/ontologias_customizadas/.
# =============================================================================

import re
import sys
import unicodedata
from pathlib import Path
 
# =============================================================================
# Funciones auxiliares
# =============================================================================
 
def identificador(nombre: str) -> str:
    """
    Convierte texto en un identificador CamelCase seguro para Turtle.
    Elimina caracteres no alfanuméricos para producir IRIs válidos y ordenados.
    """ 
    nombre = unicodedata.normalize("NFD", nombre)
    nombre = "".join(c for c in nombre if unicodedata.category(c) != "Mn")
    nombre = re.sub(r"[^\w\s\-]", "", nombre, flags=re.UNICODE)
    segmentos = re.split(r"[\s\-_]+", nombre.strip())
    return "".join(s.capitalize() for s in segmentos if s)
 
def slug(nombre: str) -> str:
    """
    Convierte el nombre de la baraja en un slug minúscula apto para IRIs y nombres de archivo.
    Los espacios se reemplazan por guiones bajos y se eliminan los caracteres
    que no son alfanuméricos ni guiones bajos.
    """
    nombre = unicodedata.normalize("NFD", nombre)
    nombre = "".join(c for c in nombre if unicodedata.category(c) != "Mn")
    nombre = nombre.lower().strip()
    nombre = re.sub(r"\s+", "_", nombre)
    nombre = re.sub(r"[^\w]", "", nombre)
    return nombre
 
def etiqueta(nombre: str) -> str:
    """
    Devuelve una etiqueta legible para rdfs:label.
    """
    return nombre.strip().capitalize()
 
# =============================================================================
# Bloques de la ontología
# =============================================================================
 
def encabezado(iri_base: str, nombre_baraja: str, n_palos: int, n_rangos: int) -> str:
    """
    Construye los prefijos Turtle, los metadatos OWL y el resumen de cardinalidades.
 
    Incluye además una breve explicación de por qué se usan owl:oneOf y owl:AllDifferent
    para cerrar las clases y garantizar la unicidad de los individuos bajo OWA.
    """
    n_cartas = n_palos * n_rangos
    return f"""\
# =============================================================================
# Ontología de baraja: {nombre_baraja}
# Generada automáticamente por generador_ontologias.py
# =============================================================================
#
# Esta ontología modela la estructura de una baraja de cartas de tipo '{nombre_baraja}'
# en OWL 2 DL. El dominio cubre palos, rangos, cartas y la clasificación de
# manos de cinco cartas. Otros aspectos del juego quedan fuera del alcance.
#
# =============================================================================
 
@prefix poker: <{iri_base}#> .
@prefix owl:  <http://www.w3.org/2002/07/owl#> .
@prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .
 
# -----------------------------------------------------------------------------
# OWL trabaja bajo Open World Assumption (OWA): lo que no está afirmado es
# desconocido, no necesariamente falso. Sin intervención explícita, el razonador
# podría asumir la existencia de palos o rangos adicionales no declarados.
#
# Para evitarlo, Palo y Rango se cierran con owl:oneOf, fijando exactamente
# los individuos posibles. Los {n_cartas} individuos de cartas se declaran
# además AllDifferent para que el razonador los trate como entidades distintas
# y no intente unificarlas.
# -----------------------------------------------------------------------------
 
<{iri_base}>
    rdf:type owl:Ontology ;
    rdfs:label "Ontología de baraja {nombre_baraja}" ;
    rdfs:comment "Ontología OWL 2 DL que modela la baraja '{nombre_baraja}' ({n_palos} palos x {n_rangos} rangos = {n_cartas} cartas)." ;
    owl:versionInfo "2.0.0" .
"""
 
def seccion_palo(palos: list[str]) -> str:
    """
    Declara poker:Palo como clase cerrada mediante owl:oneOf.
 
    La clase se cierra con exactamente los palos recibidos; el razonador no
    podrá inferir palos adicionales.
    """
    ids_palos_owl = " ".join(f"poker:{identificador(p)}" for p in palos)
    lineas = [
        "",
        "# =============================================================================",
        "# Palos y Rangos",
        "# =============================================================================",
        "",
        "# Definición de la clase Palo.",
        "# Palo se cierra con owl:oneOf para que el razonador no asuma palos adicionales.",
        "poker:Palo a owl:Class ;",
        "    owl:equivalentClass [",
        "        a owl:Class ;",
        f"        owl:oneOf ( {ids_palos_owl} )",
        "    ] ;",
        '    rdfs:label "Palo" ;',
        f'    rdfs:comment "Palo de una carta. Clase cerrada: exactamente {", ".join(identificador(p) for p in palos)}." .',
    ]
    return "\n".join(lineas)
 
def seccion_rango(rangos: list[str]) -> str:
    """
    Declara poker:Rango como clase cerrada en el orden recibido, de menor a mayor valor.
 
    El orden de la lista determina la fuerza relativa de los rangos en los
    clasificadores de escalera y escalera real.
    """
    ids_rangos_owl = " ".join(f"poker:{identificador(r)}" for r in rangos)
    lineas = [
        "",
        "# Definición de la clase Rango.",
        "# Rango se cierra con owl:oneOf para que el razonador no asuma rangos adicionales.",
        "poker:Rango a owl:Class ;",
        "    owl:equivalentClass [",
        "        a owl:Class ;",
        f"        owl:oneOf ( {ids_rangos_owl} )",
        "    ] ;",
        '    rdfs:label "Rango" ;',
        f'    rdfs:comment "Rango de una carta. Clase cerrada: exactamente {", ".join(identificador(r) for r in rangos)}." .',
    ]
    return "\n".join(lineas)
 
def seccion_carta(palos: list[str], rangos: list[str]) -> str:
    """
    Define poker:Carta con palo y rango obligatorios.
 
    Cada carta debe tener exactamente un palo (garantizado por tienePalo como
    FunctionalProperty) y exactamente un rango (garantizado por tieneRango).
    """
    return """
# Definición de la clase Carta.
# Cada carta tiene exactamente un palo y un rango, garantizado por las FunctionalProperty definidas más adelante.
poker:Carta a owl:Class ;
    rdfs:subClassOf [
        a owl:Restriction ;
        owl:onProperty poker:tienePalo ;
        owl:someValuesFrom poker:Palo
    ] ;
    rdfs:subClassOf [
        a owl:Restriction ;
        owl:onProperty poker:tieneRango ;
        owl:someValuesFrom poker:Rango
    ] ;
    rdfs:label "Carta" ;
    rdfs:comment "Una carta de la baraja, caracterizada por un palo y un rango únicos." ."""
 
def subclases_por_palo(palos: list[str]) -> str:
    """
    Genera las clases CartaDe<Palo>, equivalentes a la restricción tienePalo value <Palo>.
 
    Estas subclases son necesarias para el clasificador de Color y Escalera de Color,
    donde la condición exige que todas las cartas de la mano sean del mismo palo.
    """
    lineas = [
        "",
        "# Subclases de Carta por palo.",
        "# Se usan en los clasificadores de Color y Escalera de Color.",
    ]
    for p in palos:
        id_palo = identificador(p)
        lineas += [
            f"poker:CartaDe{id_palo} a owl:Class ;",
            "    rdfs:subClassOf poker:Carta ;",
            "    owl:equivalentClass [",
            "        a owl:Restriction ;",
            "        owl:onProperty poker:tienePalo ;",
            f"        owl:hasValue poker:{id_palo}",
            "    ] ;",
            f'    rdfs:label "Carta de {etiqueta(p)}" ;',
            f'    rdfs:comment "Una carta de la baraja del palo de {etiqueta(p)}." .',
            "",
        ]
    return "\n".join(lineas)
 
def subclases_por_rango(rangos: list[str]) -> str:
    """
    Genera las clases CartaDe<Rango>, equivalentes a la restricción tieneRango value <Rango>.
 
    Estas subclases se usan en los clasificadores de Par, Trío y Póker, donde la
    condición es tener N cartas del mismo rango.
    """
    lineas = [
        "# Subclases de Carta por rango.",
        "# Se usan en los clasificadores de Par, Trío y Póker.",
    ]
    for r in rangos:
        id_rango = identificador(r)
        lineas += [
            f"poker:CartaDe{id_rango} a owl:Class ;",
            "    rdfs:subClassOf poker:Carta ;",
            f"    owl:equivalentClass [ a owl:Restriction ; owl:onProperty poker:tieneRango ; owl:hasValue poker:{id_rango} ] ;",
            f'    rdfs:label "Carta de {etiqueta(r)}" .',
            "",
        ]
    return "\n".join(lineas)
  
def seccion_grupos(posibles: dict[str, bool], motivos: dict[str, str]) -> str:
    """
    Define poker:Mano como un grupo de exactamente cinco cartas.

    Incluye el árbol dinámico de tipos de mano válidos para la baraja indicada,
    junto con los tipos omitidos y el motivo de cada omisión.
    """
    lineas_arbol = ["#   Mano"]
    for indice, (clave, nombre, descripcion) in enumerate(ORDEN_MANOS, start=1):
        if posibles.get(clave, False):
            lineas_arbol.append(f"#   ├── {nombre:<14} ({indice}) {descripcion}")

    omitidas = [(nombre, motivos[clave]) for clave, nombre, _ in ORDEN_MANOS if clave in motivos]
    if omitidas:
        lineas_arbol.append("#")
        lineas_arbol.append("# Tipos de mano no generados para esta baraja:")
        for nombre, motivo in omitidas:
            lineas_arbol.append(f"#   - {nombre}: {motivo}.")

    arbol = "\n".join(lineas_arbol)

    return f"""
# =============================================================================
# Tipos de Mano
# =============================================================================
#
# Jerarquía de menor a mayor valor de las manos posibles con esta baraja:
#
{arbol}
#
# Decisión de diseño: los tipos de mano no se declaran disjuntos entre sí.
# Si bien en el juego real esto es así, la ontología busca evaluar la capacidad
# de los razonadores OWL frente a ontologías suficientemente complejas. Una
# versión con clases disjuntas queda para trabajo futuro.
# =============================================================================

# Definición de la clase Mano.
poker:Mano a owl:Class ;
    rdfs:subClassOf [
        a owl:Restriction ;
        owl:onProperty poker:contieneCarta ;
        owl:maxQualifiedCardinality "5"^^xsd:nonNegativeInteger ;
        owl:onClass poker:Carta
    ] ;
    rdfs:subClassOf [
        a owl:Restriction ;
        owl:onProperty poker:contieneCarta ;
        owl:minQualifiedCardinality "5"^^xsd:nonNegativeInteger ;
        owl:onClass poker:Carta
    ] ;
    rdfs:label "Mano" ;
    rdfs:comment "La mejor combinación de 5 cartas que puede formar un jugador con la baraja." ."""
 
def seccion_propiedades() -> str:
    """
    Declara las propiedades de objeto y de datos usadas por cartas, manos y rangos.
 
    tienePalo y tieneRango son FunctionalProperty porque una carta no puede tener
    dos palos ni dos rangos simultáneamente. Junto con owl:oneOf en Palo y Rango,
    esto garantiza que cada carta sea única en la ontología.
 
    manoTienePar es una propiedad auxiliar para el clasificador de DoblePar.
    """
    return """
 
# =============================================================================
# Propiedades de Objeto
# =============================================================================
 
# Definición de la propiedad tienePalo.
# Propiedad que indica que cada carta tiene exactamente un palo.
poker:tienePalo a owl:ObjectProperty , owl:FunctionalProperty ;
    rdfs:domain poker:Carta ;
    rdfs:range  poker:Palo ;
    rdfs:label  "Tiene Palo" ;
    rdfs:comment "Propiedad que asocia una carta con su palo. Funcional: cada carta tiene exactamente un palo." .
 
# Definición de la propiedad tieneRango.
# Propiedad que indica que cada carta tiene exactamente un rango.
poker:tieneRango a owl:ObjectProperty , owl:FunctionalProperty ;
    rdfs:domain poker:Carta ;
    rdfs:range  poker:Rango ;
    rdfs:label  "Tiene Rango" ;
    rdfs:comment "Propiedad que asocia una carta con su rango. Funcional: cada carta tiene exactamente un rango." .
 
# Definición de la propiedad contieneCarta.
# Propiedad que indica que una mano contiene cierta carta.
poker:contieneCarta a owl:ObjectProperty ;
    rdfs:domain poker:Mano ;
    rdfs:range  poker:Carta ;
    rdfs:label  "Contiene Carta" ;
    rdfs:comment "Propiedad que relaciona una mano con cada una de las cartas que la componen." .
 
# Definición de la propiedad manoTienePar.
# manoTienePar es una propiedad auxiliar para el clasificador de DoblePar.
# OWL DL 2 no puede contar cuántos rangos distintos tienen cardinalidad mayor o igual a 2,
# así que esta propiedad se agrega manualmente en la ABox al instanciar cada mano.
# La explicación está detallada en la definición de la clase DoblePar.
poker:manoTienePar a owl:ObjectProperty ;
    rdfs:domain poker:Mano ;
    rdfs:range  poker:Rango ;
    rdfs:label  "Mano tiene Par" ;
    rdfs:comment "Indica qué rangos están presentes con al menos 2 cartas en la mano. Se agrega manualmente en la ABox; usado por el clasificador de DoblePar." ."""
 
def seccion_abox_palos(palos: list[str]) -> str:
    """
    Crea los individuos ABox para cada palo de la baraja.
    """
    lineas = [
        "",
        "# =============================================================================",
        "# ABox - Individuos",
        "# =============================================================================",
        "#",
        "# Convención de nombres para cartas: {Rango}De{Palo}.",
        "# =============================================================================",
        "",
        "# --- Palos ---",
    ]
    for p in palos:
        id_palo = identificador(p)
        lineas += [
            f"poker:{id_palo} a poker:Palo ;",
            f'    rdfs:label "{etiqueta(p)}" .',
        ]
    return "\n".join(lineas)
 
def seccion_abox_rangos(rangos: list[str]) -> str:
    """
    Crea los individuos ABox para cada rango de la baraja.
    """
    lineas = [
        "",
        "# --- Rangos ---",
    ]
    for r in rangos:
        id_rango = identificador(r)
        lineas += [
            f"poker:{id_rango} a poker:Rango ;",
            f'    rdfs:label "{etiqueta(r)}" .',
            "",
        ]
    return "\n".join(lineas)
 
def seccion_abox_cartas(palos: list[str], rangos: list[str]) -> str:
    """
    Crea un individuo ABox por cada combinación palo-rango de la baraja.
    """
    n_cartas = len(palos) * len(rangos)
    lineas = [
        "# --- Cartas ---",
    ]
    for p in palos:
        id_palo = identificador(p)
        lineas.append(f"# Cartas de {etiqueta(p)}.")
        for r in rangos:
            id_rango = identificador(r)
            id_carta = f"{id_rango}De{id_palo}"
            lineas += [
                f"poker:{id_carta} a poker:Carta ;",
                f"    poker:tienePalo poker:{id_palo} ; poker:tieneRango poker:{id_rango} ;",
                f'    rdfs:label "{etiqueta(r)} de {etiqueta(p)}" .',
            ]
        lineas.append("")
    return "\n".join(lineas)
 
def seccion_todos_distintos(palos: list[str], rangos: list[str]) -> str:
    """
    Declara palos, rangos y cartas como individuos mutuamente distintos.
 
    AllDifferent es necesario porque OWL DL 2 no asume distinción entre individuos
    por defecto (la Unique Name Assumption no aplica en OWL). Sin estas declaraciones,
    el razonador podría unificar, por ejemplo, dos cartas distintas si no hay
    nada que las contradiga explícitamente.
    """
    ids_palos = " ".join(f"poker:{identificador(p)}" for p in palos)
    ids_rangos = " ".join(f"poker:{identificador(r)}" for r in rangos)
 
    lineas_cartas = []
    for p in palos:
        id_palo = identificador(p)
        grupo = [f"poker:{identificador(r)}De{id_palo}" for r in rangos]
        lineas_cartas.append("        " + " ".join(grupo))
 
    bloque_cartas = "\n".join(lineas_cartas)
    n_palos = len(palos)
    n_rangos = len(rangos)
    n_cartas = n_palos * n_rangos
 
    return f"""
# --- Unicidad de individuos ---
# AllDifferent es necesario porque OWL DL 2 no asume distinción entre individuos
# por defecto (Unique Name Assumption no aplica en OWL). Aplica para palos, rangos y cartas.
 
# {n_palos} palos distintos.
[] a owl:AllDifferent ;
    owl:distinctMembers ( {ids_palos} ) .
 
# {n_rangos} rangos distintos.
[] a owl:AllDifferent ;
    owl:distinctMembers ( {ids_rangos} ) .
 
# {n_cartas} cartas distintas.
[] a owl:AllDifferent ;
    owl:distinctMembers (
{bloque_cartas}
    ) .
"""
 
# =============================================================================
# Clasificadores de Manos
# =============================================================================
 
ORDEN_MANOS = [
    ("carta_alta", "CartaAlta", "Sin combinación; gana la carta más alta"),
    ("par", "Par", "Dos cartas del mismo rango"),
    ("doble_par", "DoblePar", "Dos pares de rangos distintos"),
    ("trio", "Trio", "Tres cartas del mismo rango"),
    ("escalera", "Escalera", "Cinco cartas de rangos consecutivos"),
    ("color", "Color", "Cinco cartas del mismo palo"),
    ("full", "Full", "Un trío más un par de rangos distintos"),
    ("poker", "Poker", "Cuatro cartas del mismo rango"),
    ("escalera_color", "EscaleraColor", "Cinco cartas consecutivas del mismo palo"),
    ("escalera_real", "EscaleraReal", "Los cinco rangos más altos del mismo palo"),
]
 
def capacidades_manos(palos: list[str], rangos: list[str]) -> tuple[dict[str, bool], dict[str, str]]:
    """
    Calcula qué clasificadores de manos tienen sentido para la baraja indicada.
 
    Las reglas se derivan de la estructura física de la baraja: una carta por
    combinación palo-rango y manos de exactamente cinco cartas. Por ejemplo,
    Trío requiere al menos tres palos porque no puede haber tres cartas del
    mismo rango en una baraja con solo dos palos. Color requiere al menos cinco
    rangos para poder completar una mano de cinco cartas de un único palo.
 
    Devuelve dos diccionarios:
        posibles: clave → bool, indica si el clasificador es generable.
        motivos:  clave → str,  describe por qué un clasificador se omite.
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
        "escalera_real": hay_mano and n_rangos >= 6,
    }
 
    motivos = {}
    if not hay_mano:
        base = "la baraja tiene menos de 5 cartas"
        return posibles, {clave: base for clave in posibles if not posibles[clave]}
 
    if n_palos < 2:
        motivos["par"] = "requiere al menos 2 palos"
        motivos["doble_par"] = "requiere al menos 2 palos"
    if n_rangos < 2:
        motivos["doble_par"] = "requiere al menos 2 rangos"
        motivos["full"] = "requiere al menos 2 rangos"
    if n_palos < 3:
        motivos["trio"] = "requiere al menos 3 palos"
        motivos.setdefault("full", "requiere al menos 3 palos")
    if n_palos < 4:
        motivos["poker"] = "requiere al menos 4 palos"
    if n_rangos < 5:
        motivos["escalera"] = "requiere al menos 5 rangos"
        motivos["color"] = "requiere al menos 5 rangos por palo"
        motivos["escalera_color"] = "requiere al menos 5 rangos"
        motivos["escalera_real"] = "requiere al menos 6 rangos"
 
    return posibles, {clave: motivos[clave] for clave in posibles if not posibles[clave]}
  
def clasificador_carta_alta() -> str:
    """
    Define CartaAlta como una mano que contiene al menos una carta.
 
    La definición es intencionalmente amplia: al no declarar las clases de mano
    como disjuntas, cualquier mano puede clasificarse también como CartaAlta,
    lo que es suficiente para los propósitos de esta ontología.
    """
    lineas = [
        "",
        "# Definición de la clase CartaAlta.",
        "# Mano sin una combinación específica; gana la carta más alta. La definición es simple",
        "# a propósito: al no declarar las manos como clases disjuntas, técnicamente cualquier",
        "# tipo de mano podría clasificarse también como CartaAlta.",
        "poker:CartaAlta a owl:Class ;",
        "    owl:equivalentClass [",
        "        a owl:Class ;",
        "        owl:intersectionOf (",
        "            poker:Mano",
        "            [",
        "                a owl:Restriction ;",
        "                owl:onProperty poker:contieneCarta ;",
        "                owl:someValuesFrom poker:Carta",
        "            ]",
        "        )",
        "    ] ;",
        "    rdfs:subClassOf poker:Mano ;",
        '    rdfs:label "Carta Alta" ;',
        '    rdfs:comment "Mano formada sin combinación; la carta más alta decide el ganador." .',
    ]
    return "\n".join(lineas)
 
def clasificador_par(rangos: list[str]) -> str:
    """
    Define Par como una mano con al menos dos cartas de algún rango compartido.
 
    Se recurre a owl:unionOf sobre las subclases de rango porque OWL DL 2 no puede
    expresar la condición de "mismo rango" de forma genérica. Solo debe llamarse
    si la baraja tiene al menos dos palos.
    """
    lineas = [
        "",
        "# Definición de la clase Par.",
        "# Mano que contiene dos cartas del mismo rango. Se usa unionOf sobre las subclases",
        "# de rango porque OWL DL 2 no puede expresar «mismo rango» de forma genérica.",
        "poker:Par a owl:Class ;",
        "    owl:equivalentClass [",
        "        a owl:Class ;",
        "        owl:intersectionOf (",
        "            poker:Mano",
        "            [",
        "                a owl:Class ;",
        "                owl:unionOf (",
    ]
    for r in rangos:
        id_rango = identificador(r)
        lineas.append(
            f'                    [ a owl:Restriction ; owl:onProperty poker:contieneCarta ; owl:minQualifiedCardinality "2"^^xsd:nonNegativeInteger ; owl:onClass poker:CartaDe{id_rango} ]'
        )
    lineas += [
        "                )",
        "            ]",
        "        )",
        "    ] ;",
        '    rdfs:label "Par" ;',
        '    rdfs:comment "Mano formada por dos cartas del mismo rango más tres cartas de rangos distintos." .',
    ]
    return "\n".join(lineas)
 
 
def clasificador_doble_par(rangos: list[str]) -> str:
    """
    Define DoblePar a partir de la propiedad auxiliar manoTienePar.
 
    OWL DL 2 no puede contar cuántos rangos distintos tienen cardinalidad mayor
    o igual a 2, así que esta propiedad se agrega manualmente en la ABox al
    instanciar cada mano. El clasificador exige al menos dos valores distintos
    para esa propiedad.
    """
    lineas = [
        "",
        "# Definición de la clase DoblePar.",
        "# Mano que contiene dos pares de cartas de distintos rangos. Usa la propiedad auxiliar",
        "# manoTienePar, que se agrega manualmente en la ABox. OWL DL 2 no puede contar pares",
        "# «distintos» de forma nativa, así que se delega parte del trabajo al momento de",
        "# instanciar la mano.",
        "poker:DoblePar a owl:Class ;",
        "    owl:equivalentClass [",
        "        a owl:Class ;",
        "        owl:intersectionOf (",
        "            poker:Mano",
        "            [ a owl:Restriction ;",
        "              owl:onProperty poker:manoTienePar ;",
        '              owl:minCardinality "2"^^xsd:nonNegativeInteger ]',
        "        )",
        "    ] ;",
        '    rdfs:label "Doble Par" ;',
        '    rdfs:comment "Mano formada por dos pares de rangos distintos, independientemente del palo." .',
    ]
    return "\n".join(lineas)
 
def clasificador_trio(rangos: list[str]) -> str:
    """
    Define Trío como una mano con al menos tres cartas de algún rango compartido.
 
    Se recurre a owl:unionOf sobre las subclases de rango por el mismo motivo que Par.
    Solo debe llamarse si la baraja tiene al menos tres palos.
    """
    lineas = [
        "",
        "# Definición de la clase Trio.",
        "# Mano que contiene tres cartas del mismo rango. Se usa unionOf sobre las subclases",
        "# de rango porque OWL DL 2 no puede expresar «mismo rango» de forma genérica.",
        "poker:Trio a owl:Class ;",
        "    owl:equivalentClass [",
        "        a owl:Class ;",
        "        owl:intersectionOf (",
        "            poker:Mano",
        "            [",
        "                a owl:Class ;",
        "                owl:unionOf (",
    ]
    for r in rangos:
        id_rango = identificador(r)
        lineas.append(
            f'                    [ a owl:Restriction ; owl:onProperty poker:contieneCarta ; owl:minQualifiedCardinality "3"^^xsd:nonNegativeInteger ; owl:onClass poker:CartaDe{id_rango} ]'
        )
    lineas += [
        "                )",
        "            ]",
        "        )",
        "    ] ;",
        '    rdfs:label "Trío" ;',
        '    rdfs:comment "Mano formada por tres cartas del mismo rango y otras dos cartas distintas." .',
    ]
    return "\n".join(lineas)
 
def clasificador_escalera(rangos: list[str]) -> str:
    """
    Define Escalera como la unión de todas las ventanas consecutivas de cinco rangos.
 
    Requiere que rangos esté ordenado de menor a mayor valor, porque cada ventana
    se toma directamente desde esa lista. El número de ventanas es n_rangos - 4.
 
    No hay forma de expresar "consecutivos" en OWL DL 2 sin enumerar las combinaciones,
    a menos que se especifiquen directamente qué cartas componen la mano.
    """
    n_rangos_total = len(rangos)
    secuencias = [rangos[i:i+5] for i in range(n_rangos_total - 4)]
 
    def bloque_secuencia(secuencia: list[str]) -> str:
        """Serializa una ventana de cinco rangos como intersección OWL."""
        nombre_secuencia = "-".join(etiqueta(r) for r in secuencia)
        restricciones = "\n".join(
            f'                        [ a owl:Restriction ; owl:onProperty poker:contieneCarta ; owl:someValuesFrom poker:CartaDe{identificador(r)} ]'
            for r in secuencia
        )
        return (
            f'                    # Escalera {nombre_secuencia}.\n'
            f'                    [ a owl:Class ; owl:intersectionOf (\n'
            f'{restricciones}\n'
            f'                    )]'
        )
 
    lineas = [
        "",
        "# Definición de la clase Escalera.",
        "# Mano que contiene cinco cartas con rangos consecutivos, puede ser de palos distintos.",
        "# Se enumeran todas las ventanas posibles de cinco rangos consecutivos.",
        "# No hay forma de expresar «consecutivos» en OWL DL 2 sin esta enumeración.",
        "poker:Escalera a owl:Class ;",
        "    owl:equivalentClass [",
        "        a owl:Class ;",
        "        owl:intersectionOf (",
        "            poker:Mano",
        "            [",
        "                a owl:Class ;",
        "                owl:unionOf (",
    ]
    for secuencia in secuencias:
        lineas.append(bloque_secuencia(secuencia))
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
    """
    Define Color como una mano en la que todas las cartas son del mismo palo.
 
    Se usa owl:allValuesFrom por palo porque la condición es que todas las cartas
    de la mano pertenezcan a un único palo, no solo algunas.
    """
    lineas = [
        "",
        "# Definición de la clase Color.",
        "# Mano que contiene cinco cartas del mismo palo, con rangos distintos.",
        "# Se usa allValuesFrom porque la condición exige que todas las cartas sean del mismo palo.",
        "poker:Color a owl:Class ;",
        "    owl:equivalentClass [",
        "        a owl:Class ;",
        "        owl:intersectionOf (",
        "            poker:Mano",
        "            [",
        "                a owl:Class ;",
        "                owl:unionOf (",
    ]
    for p in palos:
        id_palo = identificador(p)
        lineas.append(
            f'                    [ a owl:Restriction ; owl:onProperty poker:contieneCarta ; owl:allValuesFrom poker:CartaDe{id_palo} ]'
        )
    lineas += [
        "                )",
        "            ]",
        "        )",
        "    ] ;",
        '    rdfs:label "Color" ;',
        '    rdfs:comment "Mano formada por cinco cartas del mismo palo, no necesariamente consecutivas entre sí." .',
    ]
    return "\n".join(lineas)
 
def clasificador_full() -> str:
    """
    Define Full como la intersección de Trío y DoblePar.
 
    Al no declarar las manos como clases disjuntas, este patrón es conceptualmente
    correcto: asegura un trío y un par de rangos distintos en la misma mano, en
    analogía con EscaleraColor ≡ Escalera ⊓ Color.
    """
    return """
# Definición de la clase Full.
# Mano que contiene un trío más un par de rangos distintos. Al no declarar las manos
# como clases disjuntas, Full puede definirse como la intersección de Trio y DoblePar,
# lo que es conceptualmente correcto y evita duplicar restricciones.
poker:Full a owl:Class ;
    owl:equivalentClass [
        a owl:Class ;
        owl:intersectionOf (
            poker:Trio
            poker:DoblePar
        )
    ] ;
    rdfs:label "Full" ;
    rdfs:comment "Mano formada por tres cartas del mismo rango y dos cartas de otro mismo rango." ."""
  
def clasificador_poker_mano(rangos: list[str]) -> str:
    """
    Define Póker como una mano con al menos cuatro cartas de algún rango compartido.
 
    Solo debe llamarse si la baraja tiene al menos cuatro palos.
    """
    lineas = [
        "",
        "# Definición de la clase Poker.",
        "# Mano que contiene cuatro cartas del mismo rango. Se usa unionOf sobre las subclases",
        "# de rango porque OWL DL 2 no puede expresar «mismo rango» de forma genérica.",
        "poker:Poker a owl:Class ;",
        "    owl:equivalentClass [",
        "        a owl:Class ;",
        "        owl:intersectionOf (",
        "            poker:Mano",
        "            [",
        "                a owl:Class ;",
        "                owl:unionOf (",
    ]
    for r in rangos:
        id_rango = identificador(r)
        lineas.append(
            f'                    [ a owl:Restriction ; owl:onProperty poker:contieneCarta ; owl:minQualifiedCardinality "4"^^xsd:nonNegativeInteger ; owl:onClass poker:CartaDe{id_rango} ]'
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
    Define Escalera de Color como la intersección de Escalera y Color.
 
    Este patrón evita enumerar todas las combinaciones de secuencia y palo,
    en analogía directa con Full ≡ Trío ⊓ DoblePar.
    """
    return """
# Definición de la clase EscaleraColor.
# Mano que contiene cinco cartas consecutivas del mismo palo. Se define como la
# intersección de Escalera y Color, lo que es conceptualmente correcto y evita
# enumerar todas las combinaciones posibles de secuencia y palo.
poker:EscaleraColor a owl:Class ;
    owl:equivalentClass [
        a owl:Class ;
        owl:intersectionOf (
            poker:Escalera
            poker:Color
        )
    ] ;
    rdfs:label "Escalera de Color" ;
    rdfs:comment "Mano formada por cinco cartas consecutivas del mismo palo." ."""
 
def clasificador_escalera_real(rangos: list[str]) -> str:
    """
    Define Escalera Real como EscaleraColor restringida a los cinco rangos más altos.
 
    Asume que rangos está ordenado de menor a mayor valor; por eso toma los últimos
    cinco elementos de la lista. Es un caso particular de EscaleraColor.
    """
    cinco_mayores = rangos[-5:]
    restricciones = "\n".join(
        f'            [ a owl:Restriction ; owl:onProperty poker:contieneCarta ; owl:someValuesFrom poker:CartaDe{identificador(r)} ]'
        for r in cinco_mayores
    )
    nombre_cinco_mayores = "-".join(etiqueta(r) for r in cinco_mayores)
    return f"""
# Definición de la clase EscaleraReal.
# Caso especial de EscaleraColor con los cinco rangos más altos ({nombre_cinco_mayores}).
# Se define como la intersección de EscaleraColor con la presencia obligatoria
# de cada uno de esos cinco rangos.
poker:EscaleraReal a owl:Class ;
    rdfs:subClassOf poker:EscaleraColor ;
    owl:equivalentClass [
        a owl:Class ;
        owl:intersectionOf (
            poker:EscaleraColor
{restricciones}
        )
    ] ;
    rdfs:label "Escalera Real" ;
    rdfs:comment "Mano formada por los cinco rangos más altos consecutivos ({nombre_cinco_mayores}) del mismo palo." ."""
 
# =============================================================================
# Ensamblaje final
# =============================================================================
 
def generar_ontologia(
    nombre_baraja: str,
    iri_base: str,
    palos: list[str],
    rangos: list[str],
) -> str:
    """
    Ensambla la ontología completa en formato Turtle.
 
    palos y rangos deben venir validados por el llamador. Los clasificadores de
    manos se incluyen solo cuando la cantidad de palos, rangos y cartas permite
    formar físicamente esa combinación con la baraja indicada.
    """
    posibles, motivos = capacidades_manos(palos, rangos)
 
    partes = [
        encabezado(iri_base, nombre_baraja, len(palos), len(rangos)),
        seccion_palo(palos),
        seccion_rango(rangos),
        seccion_carta(palos, rangos),
        subclases_por_palo(palos),
        subclases_por_rango(rangos),
        seccion_grupos(posibles, motivos),
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
        seccion_todos_distintos(palos, rangos),
    ]
    return "\n".join(partes)
 
# =============================================================================
# Interfaz interactiva
# =============================================================================
 
def pedir(prompt: str, valor_por_defecto: str = "") -> str:
    """
    Lee una cadena desde la consola y devuelve valor_por_defecto si la entrada está vacía.
    """
    sufijo = f" [{valor_por_defecto}]" if valor_por_defecto else ""
    entrada = input(f"{prompt}{sufijo}: ").strip()
    return entrada if entrada else valor_por_defecto
 
def pedir_lista(prompt: str, ejemplo: str) -> list[str]:
    """
    Lee una lista separada por comas, limpiando espacios y elementos vacíos.
    """
    entrada = input(f"{prompt} [ej: {ejemplo}]: ").strip()
    return [elemento.strip() for elemento in entrada.split(",") if elemento.strip()]
 
def main() -> None:
    """
    Ejecuta la interfaz interactiva y escribe el archivo Turtle resultante.
 
    La IRI base se genera automáticamente a partir del nombre de la baraja,
    por lo que el usuario solo necesita indicar nombre, palos y rangos.
    El archivo de salida se guarda en ontologias/ontologias_customizadas/
    con un nombre derivado también del nombre de la baraja.
    """
    print("=" * 60)
    print("  Generador de Ontología de Baraja (OWL 2 DL / Turtle)")
    print("=" * 60)
    print()
 
    nombre_baraja = pedir("Nombre de la baraja", "MiBaraja")
    slug_baraja = slug(nombre_baraja)
    iri_base = f"http://www.ontologia-baraja.org/{slug_baraja}"
 
    print(f"  IRI base generada: {iri_base}")
    print()
 
    palos = pedir_lista(
        "Palos (separados por coma, en el orden que prefieras)",
        "Tréboles, Picas, Espadas, Corazones"
    )
    if len(palos) < 1:
        print("Error: se debe definir al menos 1 palo.")
        sys.exit(1)
 
    print()
    rangos = pedir_lista(
        "Rangos (separados por coma, de menor a mayor valor)",
        "As, Dos, Tres, Cuatro, Cinco, Seis, Siete, Jota, Reina, Rey"
    )
    if len(rangos) < 1:
        print("Error: se debe definir al menos 1 rango.")
        sys.exit(1)
 
    print()
    print(f"  Palos  : {len(palos)}  → {', '.join(palos)}")
    print(f"  Rangos : {len(rangos)}  → {', '.join(rangos)}")
    print(f"  Cartas : {len(palos) * len(rangos)}")
    print()
 
    ttl = generar_ontologia(nombre_baraja, iri_base, palos, rangos)
 
    directorio_salida = Path(__file__).parent.parent / "ontologias" / "ontologias_customizadas"
    directorio_salida.mkdir(parents=True, exist_ok=True)
    ruta_salida = directorio_salida / f"{slug_baraja}.ttl"
    ruta_salida.write_text(ttl, encoding="utf-8")
    print(f"Ontología generada: {ruta_salida.resolve()}")

# =============================================================================
# Punto de entrada
# =============================================================================
 
if __name__ == "__main__":
    main()