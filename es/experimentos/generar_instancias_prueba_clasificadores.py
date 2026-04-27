"""
generar_instancias_prueba.py
============================
Genera un archivo .ttl con una instancia de prueba por cada clasificación
de mano de Texas Hold'em, siguiendo la estructura de la ontología base
(ontologia_base_poker.ttl v2.0.0) y sus clasificadores.

Instancias generadas (13 en total):
  01 - Carta Alta         (A-K-Q-J-9 mixtos)
  02 - Par                (A-A-K-Q-J mixtos)
  03 - Doble Par          (A-A-K-K-Q mixtos)
  04 - Trío               (A-A-A-K-Q mixtos)
  05 - Escalera           (A-K-Q-J-10 mixtos, escalera alta)
  06 - Escalera Baja      (A-2-3-4-5 mixtos, rueda — caso borde)
  07 - Color              (A-K-Q-J-9 de Picas)
  08 - Full House         (A-A-A-K-K mixtos)
  09 - Póker              (A-A-A-A-K mixtos)
  10 - Escalera de Color  (9-10-J-Q-K de Corazones)
  11 - Escalera Real      (10-J-Q-K-A de Picas)
  + 2 casos borde adicionales:
  12 - Escalera media     (5-6-7-8-9 mixtos)
  13 - Color con As bajo  (A-2-3-4-6 de Diamantes, Color pero NO escalera)

Uso:
    python generar_instancias_prueba.py
    python generar_instancias_prueba.py --output mi_archivo.ttl
"""

import argparse
from datetime import date

# ---------------------------------------------------------------------------
# Configuración de prefijos y base IRI
# ---------------------------------------------------------------------------

POKER_NS  = "http://www.poker-ontology.org/poker#"
TEST_NS   = "http://www.poker-ontology.org/pruebas#"
CLS_NS    = "http://www.poker-ontology.org/clasificadores#"

PREFIXES = f"""\
@prefix poker: <{POKER_NS}> .
@prefix test:  <{TEST_NS}> .
@prefix cls:   <{CLS_NS}> .
@prefix owl:   <http://www.w3.org/2002/07/owl#> .
@prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .
"""

# ---------------------------------------------------------------------------
# Mapeo de cartas a individuos de la ontología base
# Convención: {Rango}De{Palo}  (igual que en la ABox de la base)
# ---------------------------------------------------------------------------

CARTA_IRI = {
    # Picas
    ("As",    "Picas"):     "poker:AsDePicas",
    ("Rey",   "Picas"):     "poker:ReyDePicas",
    ("Reina", "Picas"):     "poker:ReinaDePicas",
    ("Jota",  "Picas"):     "poker:JotaDePicas",
    ("Diez",  "Picas"):     "poker:DiezDePicas",
    ("Nueve", "Picas"):     "poker:NueveDePicas",
    ("Ocho",  "Picas"):     "poker:OchoDePicas",
    ("Siete", "Picas"):     "poker:SieteDePicas",
    ("Seis",  "Picas"):     "poker:SeisDePicas",
    ("Cinco", "Picas"):     "poker:CincoDePicas",
    ("Cuatro","Picas"):     "poker:CuatroDePicas",
    ("Tres",  "Picas"):     "poker:TresDePicas",
    ("Dos",   "Picas"):     "poker:DosDePicas",
    # Corazones
    ("As",    "Corazones"): "poker:AsDeCorazones",
    ("Rey",   "Corazones"): "poker:ReyDeCorazones",
    ("Reina", "Corazones"): "poker:ReinaDeCorazones",
    ("Jota",  "Corazones"): "poker:JotaDeCorazones",
    ("Diez",  "Corazones"): "poker:DiezDeCorazones",
    ("Nueve", "Corazones"): "poker:NueveDeCorazones",
    ("Ocho",  "Corazones"): "poker:OchoDeCorazones",
    ("Siete", "Corazones"): "poker:SieteDeCorazones",
    ("Seis",  "Corazones"): "poker:SeisDeCorazones",
    ("Cinco", "Corazones"): "poker:CincoDeCorazones",
    ("Cuatro","Corazones"): "poker:CuatroDeCorazones",
    ("Tres",  "Corazones"): "poker:TresDeCorazones",
    ("Dos",   "Corazones"): "poker:DosDeCorazones",
    # Diamantes
    ("As",    "Diamantes"): "poker:AsDeDiamantes",
    ("Rey",   "Diamantes"): "poker:ReyDeDiamantes",
    ("Reina", "Diamantes"): "poker:ReinaDeDiamantes",
    ("Jota",  "Diamantes"): "poker:JotaDeDiamantes",
    ("Diez",  "Diamantes"): "poker:DiezDeDiamantes",
    ("Nueve", "Diamantes"): "poker:NueveDeDiamantes",
    ("Ocho",  "Diamantes"): "poker:OchoDeDiamantes",
    ("Siete", "Diamantes"): "poker:SieteDeDiamantes",
    ("Seis",  "Diamantes"): "poker:SeisDeDiamantes",
    ("Cinco", "Diamantes"): "poker:CincoDeDiamantes",
    ("Cuatro","Diamantes"): "poker:CuatroDeDiamantes",
    ("Tres",  "Diamantes"): "poker:TresDeDiamantes",
    ("Dos",   "Diamantes"): "poker:DosDeDiamantes",
    # Tréboles
    ("As",    "Treboles"):  "poker:AsDeTreboles",
    ("Rey",   "Treboles"):  "poker:ReyDeTreboles",
    ("Reina", "Treboles"):  "poker:ReinaDeTreboles",
    ("Jota",  "Treboles"):  "poker:JotaDeTreboles",
    ("Diez",  "Treboles"):  "poker:DiezDeTreboles",
    ("Nueve", "Treboles"):  "poker:NueveDeTreboles",
    ("Ocho",  "Treboles"):  "poker:OchoDeTreboles",
    ("Siete", "Treboles"):  "poker:SieteDeTreboles",
    ("Seis",  "Treboles"):  "poker:SeisDeTreboles",
    ("Cinco", "Treboles"):  "poker:CincoDeTreboles",
    ("Cuatro","Treboles"):  "poker:CuatroDeTreboles",
    ("Tres",  "Treboles"):  "poker:TresDeTreboles",
    ("Dos",   "Treboles"):  "poker:DosDeTreboles",
}

# Clasificaciones → IRI del individuo en la ABox de la base
CLASIFICACION_IRI = {
    "CartaAlta":       "poker:ClasificacionCartaAlta",
    "Par":             "poker:ClasificacionPar",
    "DoblePar":        "poker:ClasificacionDoblePar",
    "Trio":            "poker:ClasificacionTrio",
    "Escalera":        "poker:ClasificacionEscalera",
    "Color":           "poker:ClasificacionColor",
    "FullHouse":       "poker:ClasificacionFullHouse",
    "Poker":           "poker:ClasificacionPoker",
    "EscaleraColor":   "poker:ClasificacionEscaleraColor",
    "EscaleraReal":    "poker:ClasificacionEscaleraReal",
}

# ---------------------------------------------------------------------------
# Definición de instancias de prueba
# Cada entrada: (id_local, label, clasificacion, cartas, comentario)
# cartas: lista de (rango, palo)
# ---------------------------------------------------------------------------

INSTANCIAS = [
    (
        "ManoCartaAlta_01",
        "Carta Alta: A-K-Q-J-9 (mixtos)",
        "CartaAlta",
        [("As","Picas"), ("Rey","Corazones"), ("Reina","Diamantes"), ("Jota","Treboles"), ("Nueve","Picas")],
        "Caso típico de Carta Alta: cinco rangos distintos, palos distintos, sin consecutivos completos."
    ),
    (
        "ManoPar_01",
        "Par: A-A-K-Q-J (par de Ases)",
        "Par",
        [("As","Picas"), ("As","Corazones"), ("Rey","Diamantes"), ("Reina","Treboles"), ("Jota","Picas")],
        "Par de Ases con kickers Rey, Reina, Jota."
    ),
    (
        "ManoDoblePar_01",
        "Doble Par: A-A-K-K-Q",
        "DoblePar",
        [("As","Picas"), ("As","Corazones"), ("Rey","Diamantes"), ("Rey","Treboles"), ("Reina","Picas")],
        "Doble par de Ases y Reyes con kicker Reina."
    ),
    (
        "ManoTrio_01",
        "Trío: A-A-A-K-Q",
        "Trio",
        [("As","Picas"), ("As","Corazones"), ("As","Diamantes"), ("Rey","Treboles"), ("Reina","Picas")],
        "Trío de Ases con kickers Rey y Reina."
    ),
    (
        "ManoEscalera_01",
        "Escalera: 10-J-Q-K-A (escalera alta, mixta)",
        "Escalera",
        [("Diez","Picas"), ("Jota","Corazones"), ("Reina","Diamantes"), ("Rey","Treboles"), ("As","Picas")],
        "Escalera más alta posible con palos distintos (no es EscaleraColor)."
    ),
    (
        "ManoEscalera_Rueda_01",
        "Escalera Baja (Rueda): A-2-3-4-5 (mixta) — caso borde",
        "Escalera",
        [("As","Corazones"), ("Dos","Picas"), ("Tres","Diamantes"), ("Cuatro","Treboles"), ("Cinco","Picas")],
        "Caso borde: la rueda. El As actúa como carta baja (valor 1). Palos distintos: no es EscaleraColor."
    ),
    (
        "ManoColor_01",
        "Color: A-K-Q-J-9 de Picas",
        "Color",
        [("As","Picas"), ("Rey","Picas"), ("Reina","Picas"), ("Jota","Picas"), ("Nueve","Picas")],
        "Color en Picas. Sin consecutivos completos: no es EscaleraColor."
    ),
    (
        "ManoColor_AsBajo_01",
        "Color con As bajo: A-2-3-4-6 de Diamantes — caso borde",
        "Color",
        [("As","Diamantes"), ("Dos","Diamantes"), ("Tres","Diamantes"), ("Cuatro","Diamantes"), ("Seis","Diamantes")],
        "Caso borde: Color con As bajo. No forma rueda (falta el 5), así que es solo Color."
    ),
    (
        "ManoFullHouse_01",
        "Full House: A-A-A-K-K",
        "FullHouse",
        [("As","Picas"), ("As","Corazones"), ("As","Diamantes"), ("Rey","Treboles"), ("Rey","Picas")],
        "Full house de Ases sobre Reyes."
    ),
    (
        "ManoPoker_01",
        "Póker: A-A-A-A-K",
        "Poker",
        [("As","Picas"), ("As","Corazones"), ("As","Diamantes"), ("As","Treboles"), ("Rey","Picas")],
        "Cuatro Ases con kicker Rey."
    ),
    (
        "ManoEscaleraColor_01",
        "Escalera de Color: 9-10-J-Q-K de Corazones",
        "EscaleraColor",
        [("Nueve","Corazones"), ("Diez","Corazones"), ("Jota","Corazones"), ("Reina","Corazones"), ("Rey","Corazones")],
        "Escalera de color más alta que no es Escalera Real. Carta alta: Rey de Corazones."
    ),
    (
        "ManoEscaleraColor_Rueda_01",
        "Escalera de Color Baja (Rueda): A-2-3-4-5 de Treboles — caso borde",
        "EscaleraColor",
        [("As","Treboles"), ("Dos","Treboles"), ("Tres","Treboles"), ("Cuatro","Treboles"), ("Cinco","Treboles")],
        "Caso borde: la rueda en el mismo palo. EscaleraColor pero NO EscaleraReal."
    ),
    (
        "ManoEscaleraReal_01",
        "Escalera Real: 10-J-Q-K-A de Picas",
        "EscaleraReal",
        [("Diez","Picas"), ("Jota","Picas"), ("Reina","Picas"), ("Rey","Picas"), ("As","Picas")],
        "La mano más alta posible en el póker. Única variante: solo cambia el palo."
    ),
]

# ---------------------------------------------------------------------------
# Generador de TTL
# ---------------------------------------------------------------------------

def carta_iri(rango: str, palo: str) -> str:
    key = (rango, palo)
    if key not in CARTA_IRI:
        raise ValueError(f"Carta no encontrada en la ontología base: {rango} de {palo}")
    return CARTA_IRI[key]

def clasificacion_iri(clf: str) -> str:
    if clf not in CLASIFICACION_IRI:
        raise ValueError(f"Clasificación no reconocida: {clf}")
    return CLASIFICACION_IRI[clf]

def clase_clasificacion(clf: str) -> str:
    """Devuelve el IRI de la clase OWL correspondiente a la clasificación."""
    mapa = {
        "CartaAlta":     "poker:CartaAlta",
        "Par":           "poker:Par",
        "DoblePar":      "poker:DoblePar",
        "Trio":          "poker:Trio",
        "Escalera":      "poker:Escalera",
        "Color":         "poker:Color",
        "FullHouse":     "poker:FullHouse",
        "Poker":         "poker:Poker",
        "EscaleraColor": "poker:EscaleraColor",
        "EscaleraReal":  "poker:EscaleraReal",
    }
    return mapa[clf]

def generar_bloque(inst) -> str:
    id_local, label, clasificacion, cartas, comentario = inst
    test_iri    = f"test:{id_local}"
    jugador_iri = f"test:Jugador_{id_local}"
    clf_ind     = clasificacion_iri(clasificacion)
    clf_clase   = clase_clasificacion(clasificacion)

    cartas_ttl = "\n".join(
        f"    poker:contieneCarta {carta_iri(r, p)} ;"
        for r, p in cartas
    )

    return f"""\
# --- {label} ---
# {comentario}

{jugador_iri} a poker:Jugador ;
    rdfs:label "{label} — Jugador" .

{test_iri} a poker:MejorMano , {clf_clase} ;
    rdfs:label "{label}" ;
    rdfs:comment "{comentario}" ;
    poker:tieneClasificacion {clf_ind} ;
{cartas_ttl}
    poker:tieneMejorMano {jugador_iri} .

{jugador_iri} poker:tieneMejorMano {test_iri} .
"""

def generar_alldifferent(instancias) -> str:
    iris = " ".join(f"test:{inst[0]}" for inst in instancias)
    return f"""\
# Las instancias de prueba son entidades distintas entre sí
[] a owl:AllDifferent ;
    owl:distinctMembers ( {iris} ) .
"""

def generar_ttl(instancias: list) -> str:
    hoy = date.today().isoformat()
    bloques = [generar_bloque(inst) for inst in instancias]
    alldiff = generar_alldifferent(instancias)

    cabecera = f"""\
# =============================================================================
# Instancias de Prueba — Ontología de Póker Texas Hold'em
# =============================================================================
#
# Generado por : generar_instancias_prueba.py
# Fecha        : {hoy}
# Perfil OWL   : OWL 2 DL
# Espacio de ns: {TEST_NS}
#
# Propósito
# ---------
# Una instancia representativa por clasificación de mano para verificar
# que los clasificadores infieren correctamente cada categoría.
# Incluye casos borde: rueda (escalera baja), color con As bajo,
# y la rueda como EscaleraColor.
#
# Total de instancias: {len(instancias)}
#   Clasificaciones cubiertas: CartaAlta, Par, DoblePar, Trío, Escalera (×2),
#   Color (×2), FullHouse, Póker, EscaleraColor (×2), EscaleraReal
#
# Cómo usar
# ---------
# 1. Cargar en Protégé junto con la ontología base y los clasificadores.
# 2. Ejecutar el razonador (HermiT o Pellet).
# 3. Verificar que cada instancia queda clasificada bajo la clase esperada.
# =============================================================================

{PREFIXES}
<{TEST_NS.rstrip('#')}>
    a owl:Ontology ;
    owl:imports <http://www.poker-ontology.org/poker> ;
    rdfs:label "Instancias de Prueba — Clasificadores de Mano" ;
    rdfs:comment "Una MejorMano representativa por clasificación, generada automáticamente." ;
    owl:versionInfo "1.0.0" .

"""
    return cabecera + "\n".join(bloques) + "\n" + alldiff

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Genera instancias de prueba .ttl para la ontología de póker."
    )
    parser.add_argument(
        "--output", "-o",
        default="instancias_prueba_poker.ttl",
        help="Nombre del archivo de salida (default: instancias_prueba_poker.ttl)"
    )
    args = parser.parse_args()

    ttl = generar_ttl(INSTANCIAS)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(ttl)

    print(f"✓ Generadas {len(INSTANCIAS)} instancias de prueba → {args.output}")
    print()
    print("Clasificaciones incluidas:")
    for inst in INSTANCIAS:
        print(f"  [{inst[2]:15s}]  {inst[1]}")

if __name__ == "__main__":
    main()
