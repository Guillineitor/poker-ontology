# =============================================================================
# generador_instancias_completas.py
# =============================================================================
#
# Este script genera un archivo ABox en formato Turtle (.ttl) con 40 manos
# de póker aleatorias, exactamente 4 por cada uno de los 10 tipos de mano
# del juego Texas Hold'em. Las cartas disponibles, los rangos y los palos
# se extraen dinámicamente de la ontología base que se le indique como argumento,
# por lo que el script se adapta a cualquier baraja customizada.
#
# Uso:
#     python generador_instancias_completas.py ..\(carpeta donde se ubica la ontología)\<nombre_ontología>.ttl
#
# Ejemplo:
#     python generador_instancias_completas.py ..\ontologias\ontologias_customizadas\barajas_6_rangos\baraja_6r_4p.ttl
#
# Flujo principal:
#     1. Leer la ontología TTL indicada como argumento.
#     2. Extraer dinámicamente rangos, palos y cartas de la ontología.
#     3. Verificar qué tipos de mano son generables con la baraja de cartas dada.
#     4. Generar aleatoriamente 4 manos válidas de cada uno de los 10 tipos.
#     5. Construir los bloques de la ontología de cada mano con su label descriptivo.
#     6. Escribir el archivo ABox de salida con todas las instancias de manos generadas.
#
# El archivo de salida se genera en la misma carpeta de este script,
# con el nombre derivado de la ontología de entrada.
#
# =============================================================================

import os
import re
import random
import sys
from collections import Counter


# =============================================================================
# Prefijos Turtle de cada tipo de mano, respetando los del archivo de ejemplo.
# =============================================================================

TIPOS_MANO = [
    ("carta_alta", "carta_alta", "1. Carta Alta"),
    ("par", "par", "2. Par"),
    ("doblepar", "doblepar", "3. Doble Par"),
    ("trio", "trio", "4. Trío"),
    ("escalera", "escalera", "5. Escalera"),
    ("color", "color", "6. Color"),
    ("full", "full", "7. Full"),
    ("poker", "pokerh", "8. Póker"),
    ("escalera_color", "escalera_color", "9. Escalera de Color"),
    ("escalera_real", "escalera_real", "10. Escalera Real"),
]

MANOS_POR_TIPO = 4


# =============================================================================
# Lectura de la ontología
# =============================================================================

def leer_ontologia(ruta_ontologia):
    """
    Lee la ontología indicada y extrae de ella toda la información necesaria
    para la generación de instancias: rangos en orden, palos, etiquetas cortas,
    nombres de palos para los labels, plurales de rangos y la baraja completa.
    Devuelve un diccionario con todas estas estructuras listas para usar.
    """
    with open(ruta_ontologia, encoding="utf-8") as archivo:
        contenido = archivo.read()

    m = re.search(r'@prefix\s+poker:\s*<([^>]+)>', contenido)
    uri_poker = m.group(1) if m else "http://www.poker-ontology.org/poker#"

    rangos_con_label = re.findall(
        r'poker:(\w+)\s+a\s+poker:Rango\s*;\s*rdfs:label\s+"([^"]+)"',
        contenido
    )
    rangos_sin_label = re.findall(
        r'poker:(\w+)\s+a\s+poker:Rango\b',
        contenido
    )

    etiquetas_rango = dict(rangos_con_label)
    rangos_encontrados = [(n, etiquetas_rango.get(n, n)) for n in rangos_sin_label]

    rangos = [nombre for nombre, _ in rangos_encontrados]
    valor = {rango: i for i, rango in enumerate(rangos)}
    etiqueta_rango = {nombre: label for nombre, label in rangos_encontrados}

    def pluralizar(palabra):
        """
        Devuelve el plural de una palabra en español.
        """
        vocales = "aeiouáéíóúAEIOUÁÉÍÓÚ"
        if palabra[-1] in vocales:
            return palabra + "s"
        if palabra[-1] == "z":
            return palabra[:-1] + "ces"
        return palabra + "es"

    plural_rango = {rango: pluralizar(rango) for rango in rangos}

    palos_con_label = re.findall(
        r'poker:(\w+)\s+a\s+poker:Palo\s*;\s*rdfs:label\s+"([^"]+)"',
        contenido
    )
    palos_sin_label = re.findall(
        r'poker:(\w+)\s+a\s+poker:Palo\b',
        contenido
    )
    etiquetas_palo = dict(palos_con_label)
    palos_encontrados = [(n, etiquetas_palo.get(n, n)) for n in palos_sin_label]

    palos = [nombre for nombre, _ in palos_encontrados]
    nombre_palo = {nombre: label for nombre, label in palos_encontrados}

    patron_carta = re.compile(
        r'poker:(\w+)\s+a\s+poker:Carta\s*;'
        r'.*?poker:tienePalo\s+poker:(\w+)\s*;'
        r'.*?poker:tieneRango\s+poker:(\w+)',
        re.DOTALL
    )
    baraja = []
    for m in patron_carta.finditer(contenido):
        palo = m.group(2)
        rango = m.group(3)
        if palo in set(palos) and rango in valor:
            baraja.append((rango, palo))

    if not baraja:
        raise ValueError(
            "No se encontraron cartas en la ontología. "
            "Verificá que los individuos tengan poker:tienePalo y poker:tieneRango."
        )

    print(f"  → {len(rangos)} rangos, {len(palos)} palos, {len(baraja)} cartas.")

    return {
        "uri_poker": uri_poker,
        "rangos": rangos,
        "valor": valor,
        "palos": palos,
        "etiqueta_rango": etiqueta_rango,
        "nombre_palo": nombre_palo,
        "plural_rango": plural_rango,
        "baraja": baraja,
    }


# =============================================================================
# Generadores de manos
# =============================================================================

def nombre_individuo(rango, palo):
    """
    Devuelve el nombre del individuo TTL correspondiente a una carta.
    """
    return f"{rango}De{palo}"


def es_escalera(mano, valor, rangos):
    """
    Indica si las cartas de la mano forman una escalera.
    """
    vals = sorted(valor[r] for r, _ in mano)
    secuencial = all(vals[i+1] - vals[i] == 1 for i in range(4))
    return secuencial


def firma_patron(mano, valor):
    """
    Devuelve una firma que identifica la combinación de rangos de una mano,
    independientemente del palo de cada carta. Dos manos con la misma firma
    representan el mismo valor de póker (mismos rangos y misma cantidad de
    repeticiones de cada uno), aunque los palos difieran.
    """
    return tuple(sorted(valor[r] for r, _ in mano))


def generar_mano_unica(generador, baraja, ont, cartas_usadas, patrones_usados,
                        intentos_fase1=500, intentos_fase2=5000):
    """
    Llama a generador(baraja, ont) repetidamente hasta obtener una mano
    válida que sea distinta de las ya generadas para ese mismo tipo, en dos
    niveles:

    Nivel 1 (estricta): se prioriza que la mano tenga una combinación de
    rangos  que no se haya usado todavía, para que las 4 instancias de un mismo 
    tipo se vean realmente distintas entre sí.

    Nivel 2 (flexible, para barajas pequeñas): si tras muchos intentos no se
    logra una firma de patrón nueva (porque el mazo no tiene suficientes
    combinaciones para ese tipo de mano), se acepta repetir la firma de
    patrón, pero jamás se acepta repetir la mano exacta (las mismas 5
    cartas, palo incluido).

    Si ni siquiera en la fase flexible se logra una mano con cartas exactas
    nuevas, se levanta un RuntimeError (la baraja de cartas es
    demasiado chico para producir tantas instancias distintas de ese tipo de mano).
    """
    valor = ont["valor"]

    for _ in range(intentos_fase1):
        mano, extra = generador(baraja, ont)
        cartas = frozenset(mano)
        if cartas in cartas_usadas:
            continue
        patron = firma_patron(mano, valor)
        if patron in patrones_usados:
            continue
        cartas_usadas.add(cartas)
        patrones_usados.add(patron)
        return mano, extra

    for _ in range(intentos_fase2):
        mano, extra = generador(baraja, ont)
        cartas = frozenset(mano)
        if cartas in cartas_usadas:
            continue
        patron = firma_patron(mano, valor)
        cartas_usadas.add(cartas)
        patrones_usados.add(patron)
        return mano, extra

    raise RuntimeError(
        "No se pudo generar una mano nueva de este tipo con cartas distintas "
        "a las ya generadas: la baraja de cartas es demasiado chico para producir tantas "
        "instancias distintas de este tipo de mano."
    )

def generar_carta_alta(baraja, ont):
    """
    Genera una mano de Carta Alta: cinco cartas sin ninguna combinación,
    sin escalera y sin color.
    """
    valor = ont["valor"]
    rangos = ont["rangos"]
    for _ in range(10000):
        mano = random.sample(baraja, 5)
        conteo = Counter(r for r, _ in mano)
        hay_par = any(v >= 2 for v in conteo.values())
        hay_color = len(set(p for _, p in mano)) == 1
        if not hay_par and not es_escalera(mano, valor, rangos) and not hay_color:
            return mano, None
    raise RuntimeError("No se pudo generar una mano de Carta Alta.")


def generar_par(baraja, ont):
    """
    Genera una mano de Par: exactamente dos cartas del mismo rango
    y tres kickers de rangos distintos entre sí y distintos al par.
    """
    por_rango = {}
    for carta in baraja:
        por_rango.setdefault(carta[0], []).append(carta)

    rangos_con_par = [r for r, cs in por_rango.items() if len(cs) >= 2]
    random.shuffle(rangos_con_par)

    for rango_par in rangos_con_par:
        par = random.sample(por_rango[rango_par], 2)
        usadas = set(par)
        candidatas = [c for c in baraja if c not in usadas and c[0] != rango_par]
        # Se reintenta hasta encontrar 3 descartes de rangos distintos entre sí.
        for _ in range(1000):
            descartes = random.sample(candidatas, 3)
            if len({c[0] for c in descartes}) == 3:
                return par + descartes, None
    raise RuntimeError("No se pudo generar una mano de Par.")


def generar_doble_par(baraja, ont):
    """
    Genera una mano de Doble Par: dos pares de rangos distintos y un kicker.
    Devuelve también los dos rangos emparejados para la propiedad manoTienePar.
    """
    por_rango = {}
    for carta in baraja:
        por_rango.setdefault(carta[0], []).append(carta)

    rangos_con_par = [r for r, cs in por_rango.items() if len(cs) >= 2]

    for _ in range(10000):
        r1, r2 = random.sample(rangos_con_par, 2)
        par1 = random.sample(por_rango[r1], 2)
        par2 = random.sample(por_rango[r2], 2)
        usadas = set(par1 + par2)
        candidatas = [c for c in baraja if c not in usadas and c[0] not in {r1, r2}]
        if candidatas:
            descarte = random.choice(candidatas)
            return par1 + par2 + [descarte], [r1, r2]
    raise RuntimeError("No se pudo generar una mano de Doble Par.")


def generar_trio(baraja, ont):
    """
    Genera una mano de Trío: tres cartas del mismo rango y dos kickers
    de rangos distintos entre sí y distintos al trío.
    """
    por_rango = {}
    for carta in baraja:
        por_rango.setdefault(carta[0], []).append(carta)

    rangos_con_trio = [r for r, cs in por_rango.items() if len(cs) >= 3]
    random.shuffle(rangos_con_trio)

    for rango_trio in rangos_con_trio:
        trio = random.sample(por_rango[rango_trio], 3)
        usadas = set(trio)
        candidatas = [c for c in baraja if c not in usadas and c[0] != rango_trio]
        # Se reintenta hasta encontrar 2 descartes de rangos distintos entre sí.
        for _ in range(1000):
            descartes = random.sample(candidatas, 2)
            if descartes[0][0] != descartes[1][0]:
                return trio + descartes, None
    raise RuntimeError("No se pudo generar una mano de Trío.")


def generar_escalera(baraja, ont):
    """
    Genera una mano de Escalera: cinco rangos consecutivos con palos
    mezclados (no todos iguales, para evitar que sea escalera de color).
    """
    valor = ont["valor"]
    rangos = ont["rangos"]
    conjunto = set(baraja)

    secuencias = [rangos[i:i+5] for i in range(len(rangos) - 4)]
    random.shuffle(secuencias)

    palos = ont["palos"]
    for secuencia in secuencias:
        for _ in range(500):
            mano = []
            for rango in secuencia:
                palos_disp = [p for p in palos if (rango, p) in conjunto]
                if not palos_disp:
                    break
                mano.append((rango, random.choice(palos_disp)))
            else:
                if len(set(p for _, p in mano)) > 1:
                    return mano, None
    raise RuntimeError("No se pudo generar una mano de Escalera.")


def generar_color(baraja, ont):
    """
    Genera una mano de Color: cinco cartas del mismo palo
    que no formen una escalera.
    """
    valor = ont["valor"]
    rangos = ont["rangos"]
    por_palo = {}
    for carta in baraja:
        por_palo.setdefault(carta[1], []).append(carta)

    palos_disp = [p for p, cs in por_palo.items() if len(cs) >= 5]
    random.shuffle(palos_disp)

    for palo in palos_disp:
        for _ in range(1000):
            mano = random.sample(por_palo[palo], 5)
            if not es_escalera(mano, valor, rangos):
                return mano, None
    raise RuntimeError("No se pudo generar una mano de Color.")


def generar_full(baraja, ont):
    """
    Genera una mano de Full: tres cartas de un rango y dos de otro.
    Devuelve también los dos rangos para la propiedad manoTienePar.
    """
    por_rango = {}
    for carta in baraja:
        por_rango.setdefault(carta[0], []).append(carta)

    rangos_con_trio = [r for r, cs in por_rango.items() if len(cs) >= 3]
    rangos_con_par = [r for r, cs in por_rango.items() if len(cs) >= 2]

    for _ in range(10000):
        r_trio = random.choice(rangos_con_trio)
        r_par = random.choice([r for r in rangos_con_par if r != r_trio])
        trio = random.sample(por_rango[r_trio], 3)
        par = random.sample(por_rango[r_par], 2)
        return trio + par, [r_trio, r_par]
    raise RuntimeError("No se pudo generar una mano de Full House.")


def generar_poker(baraja, ont):
    """
    Genera una mano de Póker: cuatro cartas del mismo rango y un kicker.
    """
    por_rango = {}
    for carta in baraja:
        por_rango.setdefault(carta[0], []).append(carta)

    rangos_con_poker = [r for r, cs in por_rango.items() if len(cs) >= 4]
    random.shuffle(rangos_con_poker)

    for rango in rangos_con_poker:
        cuatro = random.sample(por_rango[rango], 4)
        candidatas = [c for c in baraja if c[0] != rango]
        if candidatas:
            descarte = random.choice(candidatas)
            return list(cuatro) + [descarte], None
    raise RuntimeError("No se pudo generar una mano de Póker.")


def generar_escalera_color(baraja, ont):
    """
    Genera una mano de Escalera de Color: cinco cartas consecutivas del mismo
    palo, excluyendo la Escalera Real (los cinco rangos más altos).
    """
    valor = ont["valor"]
    rangos = ont["rangos"]
    palos = ont["palos"]
    conjunto = set(baraja)

    secuencias = [rangos[i:i+5] for i in range(len(rangos) - 5)]
    random.shuffle(secuencias)

    palos_mezclados = palos[:]
    for secuencia in secuencias:
        random.shuffle(palos_mezclados)
        for palo in palos_mezclados:
            mano = [(r, palo) for r in secuencia]
            if all(c in conjunto for c in mano):
                return mano, None
    raise RuntimeError("No se pudo generar una mano de Escalera de Color.")


def generar_escalera_real(baraja, ont):
    """
    Genera una mano de Escalera Real: los cinco rangos más altos del mismo palo.
    """
    rangos = ont["rangos"]
    palos = ont["palos"]
    conjunto = set(baraja)

    secuencia = rangos[-5:]   # Los 5 rangos más altos de la ontología.
    palos_disp = palos[:]
    random.shuffle(palos_disp)

    for palo in palos_disp:
        mano = [(r, palo) for r in secuencia]
        if all(c in conjunto for c in mano):
            return mano, None
    raise RuntimeError("No se pudo generar una mano de Escalera Real.")


# =============================================================================
# Construcción de los bloques TTL
# =============================================================================

def notacion_corta(rangos_ordenados, etiqueta_rango):
    """
    Convierte una lista de rangos ordenados a notación corta con guiones,
    como se usa en los labels de escaleras: '3-4-5-6-7', 'A-2-3-4-5', '8-9-10-J-Q'.
    """
    return "-".join(etiqueta_rango[r] for r in rangos_ordenados)


def label_descriptivo(tipo, mano, pares_extra, ont):
    """
    Construye el rdfs:label en lenguaje natural para cada tipo de mano,
    siguiendo el estilo del archivo de instancias de referencia.
    """
    valor = ont["valor"]
    rangos = ont["rangos"]
    etiqueta_rango = ont["etiqueta_rango"]
    nombre_palo = ont["nombre_palo"]
    plural_rango = ont["plural_rango"]

    mano_ord = sorted(mano, key=lambda c: valor[c[0]], reverse=True)
    rgs = [r for r, _ in mano_ord]

    if tipo == "carta_alta":
        return f"Carta Alta de {rgs[0]} con {' '.join(rgs[1:])}"

    if tipo == "par":
        conteo = Counter(r for r, _ in mano)
        rango_par = next(r for r, c in conteo.items() if c == 2)
        kickers = sorted([r for r in rgs if r != rango_par],
                           key=lambda r: valor[r], reverse=True)
        return f"Par de {plural_rango[rango_par]} con {' '.join(kickers)}"

    if tipo == "doblepar":
        r1, r2 = sorted(pares_extra, key=lambda r: valor[r], reverse=True)
        kicker = next(r for r, _ in mano if r not in pares_extra)
        return f"Doble Par de {plural_rango[r1]} y {plural_rango[r2]} con {kicker}"

    if tipo == "trio":
        conteo = Counter(r for r, _ in mano)
        rango_trio = next(r for r, c in conteo.items() if c == 3)
        kickers = sorted([r for r in rgs if r != rango_trio],
                            key=lambda r: valor[r], reverse=True)
        return f"Trío de {plural_rango[rango_trio]} con {' '.join(kickers)}"

    if tipo == "escalera":
        vals = sorted(valor[r] for r, _ in mano)
        secuencia = [rangos[v] for v in vals]
        return f"Escalera de {notacion_corta(secuencia, etiqueta_rango)}"

    if tipo == "color":
        palo = mano[0][1]
        return f"Color de {' '.join(rgs)} de {nombre_palo[palo]}"

    if tipo == "full":
        r_trio, r_par = pares_extra
        return f"Full de Trío de {plural_rango[r_trio]} con Par de {plural_rango[r_par]}"

    if tipo == "poker":
        conteo = Counter(r for r, _ in mano)
        rango_cuatro = next(r for r, c in conteo.items() if c == 4)
        descarte_rango, descarte_palo = next((r, p) for r, p in mano if r != rango_cuatro)
        return f"Póker de {plural_rango[rango_cuatro]} con {descarte_rango} de {nombre_palo[descarte_palo]}"

    if tipo == "escalera_color":
        palo = mano[0][1]
        vals = sorted(valor[r] for r, _ in mano)
        secuencia = [rangos[v] for v in vals]
        return f"Escalera de Color {notacion_corta(secuencia, etiqueta_rango)} de {nombre_palo[palo]}"

    if tipo == "escalera_real":
        palo = mano[0][1]
        return f"Escalera Real de {nombre_palo[palo]}"

    return ""


def bloque_cabecera(ont):
    """
    Genera el encabezado completo del archivo TTL: prefijos y declaración
    de la ontología.
    """
    uri_poker = ont["uri_poker"]
    uri_import = uri_poker.rstrip("#")
    lineas = [
        "# =============================================================================",
        "# Instancias de manos de Póker Texas Hold'em",
        "# =============================================================================",
        "",
        "@prefix carta_alta: <http://www.poker-ontology.org/instancias/carta_alta#> .",
        "@prefix par: <http://www.poker-ontology.org/instancias/par#> .",
        "@prefix doblepar: <http://www.poker-ontology.org/instancias/doblepar#> .",
        "@prefix trio: <http://www.poker-ontology.org/instancias/trio#> .",
        "@prefix escalera: <http://www.poker-ontology.org/instancias/escalera#> .",
        "@prefix color: <http://www.poker-ontology.org/instancias/color#> .",
        "@prefix full: <http://www.poker-ontology.org/instancias/full#> .",
        "@prefix pokerh: <http://www.poker-ontology.org/instancias/poker#> .",
        "@prefix escalera_color: <http://www.poker-ontology.org/instancias/escalera_color#> .",
        "@prefix escalera_real: <http://www.poker-ontology.org/instancias/escalera_real#> .",
        f"@prefix poker: <{uri_poker}> .",
        "@prefix owl: <http://www.w3.org/2002/07/owl#> .",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
        "",
        "<http://www.poker-ontology.org/instancias/todas>",
        "    a owl:Ontology ;",
        f"    owl:imports <{uri_import}> ;",
        "    rdfs:label \"Instancias de manos de Póker Texas Hold'em\" ;",
        "    rdfs:comment \"ABox unificado con 40 manos de prueba, 4 por cada uno de los 10 tipos de manos de Póker Texas Hold'em.\" .",
        "",
    ]
    return "\n".join(lineas)


def bloque_mano(tipo, prefijo, numero, mano, pares_extra, ont):
    """
    Genera el bloque TTL de una mano individual.
    Si se indica pares_extra, añade la propiedad manoTienePar.
    """
    nombre = f"{prefijo}:Mano{numero}"
    cartas_tt = ", ".join(f"poker:{nombre_individuo(r, p)}" for r, p in mano)
    etiqueta = label_descriptivo(tipo, mano, pares_extra, ont)

    lineas = [
        f"{nombre} a poker:Mano ;",
        f'    rdfs:label "{etiqueta}" ;',
    ]

    if pares_extra:
        pares_tt = ", ".join(f"poker:{r}" for r in pares_extra)
        lineas.append(f"    poker:contieneCarta {cartas_tt} ;")
        lineas.append(f"    poker:manoTienePar {pares_tt} .")
    else:
        lineas.append(f"    poker:contieneCarta {cartas_tt} .")

    return "\n".join(lineas)


def bloque_all_different(prefijo, numeros):
    """
    Genera la declaración owl:AllDifferent para un grupo de manos.
    """
    miembros = " ".join(f"{prefijo}:Mano{n}" for n in numeros)
    return (
        "# Unicidad de Instancias\n"
        "[] a owl:AllDifferent ;\n"
        f"    owl:distinctMembers ( {miembros} ) ."
    )


# =============================================================================
# Generación del archivo completo
# =============================================================================

GENERADORES = {
    "carta_alta": generar_carta_alta,
    "par": generar_par,
    "doblepar": generar_doble_par,
    "trio": generar_trio,
    "escalera": generar_escalera,
    "color": generar_color,
    "full": generar_full,
    "poker": generar_poker,
    "escalera_color": generar_escalera_color,
    "escalera_real": generar_escalera_real,
}


def generar_archivo(ruta_ontologia):
    """
    Función principal. Lee la ontología indicada, extrae rangos y palos,
    genera las 40 manos aleatorias y escribe el archivo TTL de salida.
    """
    nombre_base = os.path.splitext(os.path.basename(ruta_ontologia))[0]
    ruta_salida = f"instancias_{nombre_base}.ttl"
    print(f"Leyendo ontología: {ruta_ontologia}")
    ont = leer_ontologia(ruta_ontologia)
    baraja = ont["baraja"]

    secciones = [bloque_cabecera(ont)]
    numero_mano = 1

    for tipo, prefijo, titulo in TIPOS_MANO:
        seccion = [
            "# =============================================================================",
            f"# {titulo}",
            "# =============================================================================",
            "",
        ]
        numeros = []
        cartas_usadas = set()
        patrones_usados = set()

        for _ in range(MANOS_POR_TIPO):
            try:
                mano, pares = generar_mano_unica(
                    GENERADORES[tipo], baraja, ont, cartas_usadas, patrones_usados
                )
            except RuntimeError as e:
                raise RuntimeError(
                    f"{titulo}: se generaron {len(numeros)} de {MANOS_POR_TIPO} "
                    f"manos distintas y luego falló ({e})"
                ) from e

            seccion.append(bloque_mano(tipo, prefijo, numero_mano, mano, pares, ont))
            seccion.append("")
            numeros.append(numero_mano)

            print(f"  {titulo:25s} Mano{numero_mano}: {label_descriptivo(tipo, mano, pares, ont)}")
            numero_mano += 1

        seccion.append(bloque_all_different(prefijo, numeros))
        seccion.append("")
        secciones.append("\n".join(seccion))

    contenido = "\n".join(secciones)

    with open(ruta_salida, "w", encoding="utf-8") as archivo:
        archivo.write(contenido)

    print(f"\n Archivo generado: {ruta_salida}  ({numero_mano - 1} manos en total)")


# =============================================================================
# Punto de entrada
# =============================================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python generador_instancias_completas.py <ontologia.ttl>")
        sys.exit(1)

    generar_archivo(sys.argv[1])