# =============================================================================
# generar_graficos.py
# =============================================================================
#
# Este script recorre automáticamente la carpeta resultados/ con los resultados 
# los experimentos generada por ejecutar_benchmark.ps1 y BenchmarkOWLDefinitivo.java 
# (instancias_completas e instancias_divididas), consolida todos los CSV de benchmark en un 
# único DataFrame y genera una carpeta resultados/graficos/, con los gráficos de tiempo
# y memoria por razonador, tanto a en pruebas globales (instancias_completas) como
# desglosados por tipo de mano (instancias_divididas).
#
# Uso:
#     python generar_graficos.py
#
# Flujo principal:
#     1. Recorrer resultados/instancias_completas y resultados/instancias_divididas
#        buscando todos los archivos *_benchmark_*.csv.
#     2. Extraer de la ruta y el nombre de cada archivo la cantidad de rangos,
#        de palos y el tipo de mano (o "Todas" para instancias_completas).
#     3. Leer la sección "RESUMEN DE METRICAS POR RAZONADOR" de cada CSV y
#        consolidar todo en un único DataFrame, marcando TIMEOUT y errores.
#     4. Guardar ese DataFrame consolidado como resumen_metricas_global.csv.
#     5. Generar los gráficos de tiempo/memoria vs escala y los heatmaps,
#        tanto para las pruebas con instancias_completas como para 
#        instancias_divididas.
#
# Requiere: pandas, numpy, matplotlib  (pip install pandas numpy matplotlib)
#
# =============================================================================

import argparse
import csv
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.ticker as mticker

# =============================================================================
# Configuración general
# =============================================================================

RAZONADORES = ["HermiT", "JFact (FaCT++)", "Openllet (Pellet)"]

COLOR_RAZONADOR = {
    "HermiT": "#1f77b4",
    "JFact (FaCT++)": "#ff7f0e",
    "Openllet (Pellet)": "#2ca02c",
}

ORDEN_TIPOS_MANO = [
    "Todas", "CartaAlta", "Par", "DoblePar", "Trio",
    "Escalera", "Color", "Full", "Poker", "EscaleraColor", "EscaleraReal",
]

MAPA_TIPO_MANO = {
    "todas": "Todas",
    "carta_alta": "CartaAlta",
    "par": "Par",
    "doble_par": "DoblePar",
    "trio": "Trio",
    "escalera": "Escalera",
    "color": "Color",
    "full": "Full",
    "poker": "Poker",
    "escalera_color": "EscaleraColor",
    "escalera_real": "EscaleraReal",
}

PATRON_ARCHIVO = re.compile(
    r"^baraja_(?P<rangos>\d+)r_(?P<palos>\d+)p_(?P<tipo>.+)_benchmark_[\d_]+\.csv$"
)

CAMPOS_NUMERICOS = [
    "carga_ms", "init_ms", "precomp_ms", "total_ms", "mem_pico_mb",
    "clases_jerarquia", "total_inferencias",
]

CLASES_MANO_CSV = [
    "CartaAlta", "Par", "DoblePar", "Trio", "Escalera",
    "Color", "Full", "Poker", "EscaleraColor", "EscaleraReal",
]

# =============================================================================
# Parseo de CSV y construcción del DataFrame consolidado
# =============================================================================

def parsear_metadatos_ruta(path: Path):
    """
    Extrae tipo_instancias, rangos, palos y tipo_mano a partir de la ruta
    y el nombre de un archivo CSV de benchmark.

    tipo_instancias se determina buscando "instancias_completas" o
    "instancias_divididas" entre las carpetas de la ruta. rangos, palos y
    tipo_mano se extraen del nombre de archivo con PATRON_ARCHIVO. Devuelve
    None si el nombre no calza con el patrón esperado, para que el llamador
    pueda omitir ese archivo en vez de fallar.
    """
    partes = path.parts
    if "instancias_completas" in partes:
        tipo_instancias = "instancias_completas"
    elif "instancias_divididas" in partes:
        tipo_instancias = "instancias_divididas"
    else:
        tipo_instancias = "desconocido"

    m = PATRON_ARCHIVO.match(path.name)
    if not m:
        return None

    rangos = int(m.group("rangos"))
    palos = int(m.group("palos"))
    tipo_bruto = m.group("tipo")
    tipo_mano = MAPA_TIPO_MANO.get(tipo_bruto, tipo_bruto)

    return {
        "tipo_instancias": tipo_instancias,
        "rangos": rangos,
        "palos": palos,
        "tipo_mano": tipo_mano,
    }


def leer_seccion_metricas(path: Path):
    """
    Lee únicamente la sección "# RESUMEN DE METRICAS POR RAZONADOR" de un
    CSV de benchmark y la devuelve como lista de diccionarios (uno por fila).

    El CSV que escribe BenchmarkOWLDefinitivo.java tiene dos secciones
    separadas por una línea en blanco (métricas y clasificación individual);
    esta función se detiene apenas encuentra esa línea en blanco, así que
    nunca llega a leer la segunda sección.
    """
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        lineas = f.readlines()

    inicio = None
    for i, linea in enumerate(lineas):
        if linea.strip() == "# RESUMEN DE METRICAS POR RAZONADOR":
            inicio = i + 1
            break
    if inicio is None:
        return []

    fin = len(lineas)
    for i in range(inicio, len(lineas)):
        if lineas[i].strip() == "":
            fin = i
            break

    bloque = lineas[inicio:fin]
    lector = csv.DictReader(bloque)
    return list(lector)


def construir_dataframe(carpeta_resultados: Path) -> pd.DataFrame:
    """
    Recorre recursivamente carpeta_resultados buscando todos los archivos
    *_benchmark_*.csv, los parsea con parsear_metadatos_ruta / leer_seccion_metricas
    y arma un único DataFrame consolidado con todas las corridas encontradas.

    Cada fila del DataFrame resultante corresponde a un razonador dentro de
    un CSV puntual (una combinación de variante x tipo de mano). Los casos
    TIMEOUT y ERROR quedan marcados en las columnas es_timeout / es_error en
    vez de intentar convertir el texto "TIMEOUT" a un número, y los campos
    numéricos correspondientes quedan como NaN.
    """
    filas = []
    archivos = sorted(carpeta_resultados.rglob("*_benchmark_*.csv"))

    if not archivos:
        print(f"[!] No se encontraron CSV de benchmark bajo {carpeta_resultados}")
        return pd.DataFrame()

    omitidos = 0
    for archivo in archivos:
        meta = parsear_metadatos_ruta(archivo)
        if meta is None:
            print(f"[!] Nombre de archivo no reconocido, se omite: {archivo}")
            omitidos += 1
            continue

        registros = leer_seccion_metricas(archivo)
        if not registros:
            print(f"[!] Sin sección de métricas, se omite: {archivo}")
            omitidos += 1
            continue

        for r in registros:
            fila = dict(meta)
            fila["razonador"] = r.get("razonador")
            fila["archivo"] = str(archivo)

            es_timeout = (r.get("total_ms") == "TIMEOUT")
            consistente_bruto = r.get("consistente")
            es_error = (not es_timeout) and (consistente_bruto not in ("true", "false"))

            fila["es_timeout"] = es_timeout
            fila["es_error"] = es_error
            fila["error_msg"] = r.get("total_ms") if es_error else None

            for campo in CAMPOS_NUMERICOS:
                val = r.get(campo)
                try:
                    fila[campo] = float(val)
                except (TypeError, ValueError):
                    fila[campo] = np.nan

            fila["consistente"] = (consistente_bruto == "true")

            for c in CLASES_MANO_CSV:
                val = r.get(f"inst_{c}")
                try:
                    fila[f"inst_{c}"] = int(val)
                except (TypeError, ValueError):
                    fila[f"inst_{c}"] = np.nan

            filas.append(fila)

    if omitidos:
        print(f"[i] {omitidos} archivo(s) omitido(s) por formato inesperado.")

    df = pd.DataFrame(filas)
    if not df.empty:
        df["total_s"] = df["total_ms"] / 1000.0
    return df

# =============================================================================
# Utilidades de graficado
# =============================================================================

def _dibujar_lineas_por_razonador(ax, sub, metrica, col_x="palos"):
    """
    Dibuja sobre un eje ya creado una línea de `metrica` vs `col_x` por cada
    razonador presente en sub (salvo los casos de TIMEOUT).

    `col_x` es la columna a usar como eje X: "palos" (por defecto, para los
    gráficos existentes) o "rangos" (para las variantes espejo que grafican
    vs. rangos en vez de vs. palos).
    """
    for razonador in RAZONADORES:
        datos_r = sub[sub["razonador"] == razonador].sort_values(col_x)
        if datos_r.empty:
            continue
        color = COLOR_RAZONADOR.get(razonador)

        ok = datos_r[~datos_r["es_timeout"]]

        if not ok.empty:
            ax.plot(ok[col_x], ok[metrica], marker="o", label=razonador, color=color)


def _graficar_metrica_vs_variable(df, metrica, ylabel, titulo_base, carpeta_salida,
                                   col_panel, col_x, etiqueta_panel, etiqueta_x,
                                   log_y=True):
    """
    Genera un PNG por cada valor único de `col_panel` presente en df,
    graficando `metrica` vs `col_x`, con una línea por razonador.

    Función genérica que arma tanto los gráficos "vs palos" (col_panel=
    "rangos", col_x="palos") como su espejo "vs rangos" (col_panel="palos",
    col_x="rangos"), para no duplicar la lógica de armado de la figura.
    """
    carpeta_salida.mkdir(parents=True, exist_ok=True)
    valores_panel = sorted(df[col_panel].unique())

    for valor_panel in valores_panel:
        sub = df[df[col_panel] == valor_panel]
        fig, ax = plt.subplots(figsize=(7, 5))

        _dibujar_lineas_por_razonador(ax, sub, metrica, col_x=col_x)

        if log_y:
            ax.set_yscale("log")
        else:
            ax.ticklabel_format(style="plain", axis="y", useOffset=False)
        valores_x = sorted(sub[col_x].unique())
        ax.set_xticks(valores_x)
        ax.set_xlabel(etiqueta_x)
        ax.set_ylabel(ylabel)
        ax.set_title(f"{titulo_base} — {valor_panel} {etiqueta_panel}")
        ax.grid(True, which="both", linestyle=":", alpha=0.5)
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(carpeta_salida / f"barajas_{valor_panel}_{etiqueta_panel}.png", dpi=150)
        plt.close(fig)


def graficar_metrica_vs_escala(df, metrica, ylabel, titulo_base, carpeta_salida, log_y=True):
    """
    Genera un PNG por cada cantidad de rangos presente en df, graficando
    `metrica` vs cantidad de palos, con una línea por razonador.

    Pensada para instancias_completas, donde cada combinación de rango x
    palo corresponde a un único CSV ("todas" las manos en un mismo archivo).
    """
    _graficar_metrica_vs_variable(
        df, metrica, ylabel, titulo_base, carpeta_salida,
        col_panel="rangos", col_x="palos",
        etiqueta_panel="rangos", etiqueta_x="Cantidad de palos", log_y=log_y,
    )


def graficar_metrica_vs_rangos(df, metrica, ylabel, titulo_base, carpeta_salida, log_y=True):
    """
    Genera un PNG por cada cantidad de palos presente en df, graficando
    `metrica` vs cantidad de rangos, con una línea por razonador.

    Es el espejo de graficar_metrica_vs_escala: misma lógica, pero con los
    roles de "palos" y "rangos" invertidos, para poder ver cómo escala cada
    razonador a medida que crece la cantidad de rangos (con la cantidad de
    palos fija), y no solo al revés.
    """
    _graficar_metrica_vs_variable(
        df, metrica, ylabel, titulo_base, carpeta_salida,
        col_panel="palos", col_x="rangos",
        etiqueta_panel="palos", etiqueta_x="Cantidad de rangos", log_y=log_y,
    )


def _graficar_comparacion_barajas_por_razonador(df, metrica, ylabel, titulo_base,
                                                 carpeta_salida, col_linea, col_x,
                                                 etiqueta_linea, etiqueta_x, log_y=True):
    """
    Genera un PNG por cada razonador, graficando `metrica` vs `col_x` con
    una línea por cada valor de `col_linea` (todas juntas en el mismo eje).

    Es el "transpuesto" de _graficar_metrica_vs_variable: en vez de un PNG
    por valor fijo de baraja con una línea por razonador, aquí se arma un
    PNG por razonador con una línea por cada baraja (cada rango o cada
    palo fijo), para comparar de un vistazo cómo escala ESE razonador en
    particular a través de todas las barajas a la vez.
    """
    carpeta_salida.mkdir(parents=True, exist_ok=True)
    valores_linea = sorted(df[col_linea].unique())
    if not valores_linea:
        return

    cmap = plt.get_cmap("viridis")
    n = len(valores_linea)
    colores = {v: cmap(i / max(n - 1, 1)) for i, v in enumerate(valores_linea)}

    for razonador in RAZONADORES:
        sub_r = df[df["razonador"] == razonador]
        if sub_r.empty:
            continue

        fig, ax = plt.subplots(figsize=(8, 5.5))

        hubo_lineas = False
        for valor_linea in valores_linea:
            datos = sub_r[sub_r[col_linea] == valor_linea].sort_values(col_x)
            ok = datos[~datos["es_timeout"]]
            if ok.empty:
                continue
            ax.plot(ok[col_x], ok[metrica], marker="o",
                    label=f"{valor_linea} {etiqueta_linea}", color=colores[valor_linea])
            hubo_lineas = True

        if not hubo_lineas:
            plt.close(fig)
            continue

        if log_y:
            ax.set_yscale("log")
        else:
            ax.ticklabel_format(style="plain", axis="y", useOffset=False)
        valores_x = sorted(sub_r[col_x].unique())
        if valores_x:
            ax.set_xticks(valores_x)
        ax.set_xlabel(etiqueta_x)
        ax.set_ylabel(ylabel)
        ax.set_title(f"{titulo_base} — {razonador}")
        ax.grid(True, which="both", linestyle=":", alpha=0.5)
        ax.legend(fontsize=8, title=etiqueta_linea.capitalize(), ncol=2)
        fig.tight_layout()
        fig.savefig(carpeta_salida / f"{_slug_razonador(razonador)}.png", dpi=150)
        plt.close(fig)


def graficar_comparacion_barajas_vs_palos(df, metrica, ylabel, titulo_base, carpeta_salida, log_y=False):
    """
    Genera un PNG por razonador, con una línea por cantidad de rangos,
    graficando `metrica` vs cantidad de palos.

    Permite ver, para un razonador dado, cómo se comportan todas las
    barajas (una por cada rango fijo) a medida que aumentan los palos,
    todas juntas en el mismo gráfico. Pensada para instancias_completas.
    """
    _graficar_comparacion_barajas_por_razonador(
        df, metrica, ylabel, titulo_base, carpeta_salida,
        col_linea="rangos", col_x="palos",
        etiqueta_linea="rangos", etiqueta_x="Cantidad de palos", log_y=log_y,
    )


def graficar_comparacion_barajas_vs_rangos(df, metrica, ylabel, titulo_base, carpeta_salida, log_y=False):
    """
    Es el espejo de graficar_comparacion_barajas_vs_palos: genera un PNG
    por razonador, con una línea por cantidad de palos, graficando
    `metrica` vs cantidad de rangos (palos fijo por línea en vez de rangos
    fijo por línea).
    """
    _graficar_comparacion_barajas_por_razonador(
        df, metrica, ylabel, titulo_base, carpeta_salida,
        col_linea="palos", col_x="rangos",
        etiqueta_linea="palos", etiqueta_x="Cantidad de rangos", log_y=log_y,
    )


def _graficar_heatmap_rangos_palos(df, carpeta_salida, metrica, cbar_label,
                                    fmt_celda, fmt_tick, titulo_metrica,
                                    razonadores=None):
    """
    Función interna genérica: genera un heatmap rangos x palos -> `metrica`,
    uno por cada razonador en `razonadores` (por defecto todos, RAZONADORES).

    Compartida por graficar_heatmap_tiempo (metrica="total_s") y
    graficar_heatmap_memoria (metrica="mem_pico_mb"), para no duplicar la
    lógica de armado de la matriz ni la normalización global de color.

    Pensada para instancias_completas. Los timeouts se muestran con achurado
    rojo y la etiqueta "TIMEOUT" sobre una celda en blanco (nunca participan
    de la escala de color), para no confundirlos jamás con un valor real
    medido ni distorsionar la escala con un valor inventado. La escala de
    color se normaliza de forma global, a partir de los valores válidos de
    TODOS los razonadores graficados en conjunto, para que los PNG
    resultantes compartan exactamente la misma barra de color y sean
    comparables entre sí.
    """
    carpeta_salida.mkdir(parents=True, exist_ok=True)
    razonadores = razonadores if razonadores is not None else RAZONADORES
    rangos_unicos = sorted(df["rangos"].unique())
    palos_unicos = sorted(df["palos"].unique())

    df_razonadores = df[df["razonador"].isin(razonadores)]
    valores_validos_global = df_razonadores.loc[~df_razonadores["es_timeout"], metrica].dropna()
    if not valores_validos_global.empty:
        vmin_global = valores_validos_global.min()
        vmax_global = valores_validos_global.max()
        norm_global = (mcolors.Normalize(vmin=vmin_global, vmax=vmax_global)
                       if vmax_global > vmin_global else None)
    else:
        norm_global = None

    for razonador in razonadores:
        sub = df[df["razonador"] == razonador]
        matriz = np.full((len(rangos_unicos), len(palos_unicos)), np.nan)
        es_to = np.zeros_like(matriz, dtype=bool)

        for i, r in enumerate(rangos_unicos):
            for j, p in enumerate(palos_unicos):
                fila = sub[(sub["rangos"] == r) & (sub["palos"] == p)]
                if fila.empty:
                    continue
                row = fila.iloc[0]
                if row["es_timeout"]:
                    es_to[i, j] = True
                else:
                    matriz[i, j] = row[metrica]

        _dibujar_heatmap_individual(
            matriz, es_to, rangos_unicos, palos_unicos,
            xlabel="Cantidad de palos", ylabel="Cantidad de rangos",
            titulo=f"{titulo_metrica} — {razonador}",
            ruta_salida=carpeta_salida / f"{_slug_razonador(razonador)}.png",
            norm=norm_global,
            cbar_label=cbar_label, fmt_celda=fmt_celda, fmt_tick=fmt_tick,
        )


def graficar_heatmap_tiempo(df, carpeta_salida, razonadores=None):
    """
    Genera un heatmap rangos x palos -> tiempo total (s), uno por razonador
    (por defecto los tres; pasar `razonadores` para restringir, por ejemplo
    a HermiT y JFact).

    Pensada para instancias_completas. Ver _graficar_heatmap_rangos_palos
    para el detalle del manejo de timeouts y la normalización de color.
    """
    _graficar_heatmap_rangos_palos(
        df, carpeta_salida, metrica="total_s",
        cbar_label="Tiempo total (s)", fmt_celda=lambda v: f"{v:.2f}s",
        fmt_tick=_formatear_tick_tiempo,
        titulo_metrica="Tiempo total de clasificacion",
        razonadores=razonadores,
    )


def graficar_heatmap_memoria(df, carpeta_salida, razonadores=None):
    """
    Genera un heatmap rangos x palos -> memoria peak (MB), uno por
    razonador. Por defecto se restringe a HermiT y JFact (los dos
    razonadores que sí completan a la escala más grande sin timeout;
    Openllet queda casi siempre marcado como TIMEOUT ahí, por lo que un
    heatmap de memoria para él aportaría poco), pero se puede pasar
    `razonadores` explícitamente para incluir a los tres.

    Es el equivalente en memoria de graficar_heatmap_tiempo: misma matriz
    rangos x palos, mismo tratamiento de TIMEOUT (celda en blanco con
    achurado rojo, memoria queda NaN igual que el tiempo en esos casos) y
    misma normalización global de color entre los PNG generados.
    """
    _graficar_heatmap_rangos_palos(
        df, carpeta_salida, metrica="mem_pico_mb",
        cbar_label="Memoria peak (MB)", fmt_celda=lambda v: f"{v:.0f} MB",
        fmt_tick=_formatear_tick_memoria,
        titulo_metrica="Memoria utilizada",
        razonadores=razonadores if razonadores is not None else ["HermiT", "JFact (FaCT++)"],
    )


def _formatear_tick_tiempo(valor, pos=None):
    """
    Formatea un tick del colorbar de tiempo como número entero.
    """
    if valor >= 1:
        return f"{int(round(valor))}"
    return f"{valor:g}"


def _formatear_tick_memoria(valor, pos=None):
    """
    Formatea un tick del colorbar de memoria (MB) como número entero.

    Usa exactamente la misma lógica de redondeo que _formatear_tick_tiempo;
    se mantiene como función separada solo para que el nombre sea claro en
    los llamados de heatmaps de memoria.
    """
    return _formatear_tick_tiempo(valor, pos)


def _dibujar_heatmap_individual(matriz, es_to, etiquetas_y, etiquetas_x,
                                 xlabel, ylabel, titulo, ruta_salida, norm=None,
                                 cbar_label="Tiempo total (s)",
                                 fmt_celda=lambda v: f"{v:.2f}s",
                                 fmt_tick=_formatear_tick_tiempo):
    """
    Dibuja y guarda un único heatmap a partir de una matriz de valores (por
    defecto tiempos en s, pero sirve para cualquier métrica numérica) y una
    matriz booleana es_to que indica qué celdas corresponden a TIMEOUT.

    Usa escala de color lineal, calculada solo a partir de los valores
    reales (no-timeout). Las celdas TIMEOUT quedan en blanco y se
    sobreescriben con achurado rojo y la etiqueta "TIMEOUT", sin participar
    nunca de la escala.

    Si se recibe `norm`, se usa esa normalización (por ejemplo una escala
    global calculada por el llamador a partir de varios heatmaps juntos)
    en vez de calcular una propia a partir de esta matriz. Esto permite que
    varios PNG generados por separado (uno por razonador) compartan
    exactamente la misma barra de color, incluso si alguno de ellos no
    tiene ningún valor válido propio (por ejemplo, si todas sus corridas
    dieron TIMEOUT).

    `cbar_label`, `fmt_celda` y `fmt_tick` permiten reutilizar exactamente
    el mismo dibujo para otras métricas (por ejemplo memoria peak en MB en
    vez de tiempo en s), sin duplicar la lógica de la figura.
    """
    fig, ax = plt.subplots(figsize=(1.1 * len(etiquetas_x) + 2, 0.9 * len(etiquetas_y) + 2))

    valores_validos = matriz[~np.isnan(matriz)]

    if norm is None and valores_validos.size:
        vmin = valores_validos.min()
        vmax = valores_validos.max()
        norm = mcolors.Normalize(vmin=vmin, vmax=vmax) if vmax > vmin else None

    im = ax.imshow(np.ma.masked_invalid(matriz), cmap="viridis", norm=norm, aspect="auto")

    for i in range(matriz.shape[0]):
        for j in range(matriz.shape[1]):
            if es_to[i, j]:
                ax.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False,
                                            hatch="//", edgecolor="red", linewidth=1.4))
                ax.text(j, i, "TIMEOUT", ha="center", va="center",
                        color="red", fontsize=7, fontweight="bold")
            elif not np.isnan(matriz[i, j]):
                ax.text(j, i, fmt_celda(matriz[i, j]), ha="center", va="center",
                        color="white", fontsize=8)

    ax.set_xticks(range(len(etiquetas_x)))
    ax.set_xticklabels(etiquetas_x)
    ax.set_yticks(range(len(etiquetas_y)))
    ax.set_yticklabels(etiquetas_y)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(titulo, fontsize=11)
    if norm is not None or valores_validos.size:
        cbar = fig.colorbar(im, ax=ax, label=cbar_label)
        cbar.ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_tick))
    fig.tight_layout()
    fig.savefig(ruta_salida, dpi=150)
    plt.close(fig)


def _graficar_pequenos_multiplos_por_tipo_mano(df, metrica, ylabel, titulo_base,
                                                carpeta_salida, col_panel, col_x,
                                                etiqueta_panel, etiqueta_x, log_y=True):
    """
    Genera un PNG por tipo de mano; cada uno con un subplot por cada valor
    de `col_panel` (una grilla de pequeños múltiplos), graficando `metrica`
    vs `col_x` dentro de cada subplot.

    Función genérica que arma tanto la grilla "vs palos" (col_panel=
    "rangos", col_x="palos") como su espejo "vs rangos" (col_panel="palos",
    col_x="rangos"), para no duplicar la lógica de armado de la figura.
    """
    carpeta_salida.mkdir(parents=True, exist_ok=True)
    tipos_presentes = [t for t in ORDEN_TIPOS_MANO
                       if t != "Todas" and t in df["tipo_mano"].unique()]
    valores_panel = sorted(df[col_panel].unique())

    ncols = 3
    nrows = int(np.ceil(len(valores_panel) / ncols)) if valores_panel else 1

    for tipo in tipos_presentes:
        sub_tipo = df[df["tipo_mano"] == tipo]
        fig, axes = plt.subplots(nrows, ncols, figsize=(4.6 * ncols, 3.6 * nrows), squeeze=False)

        for idx, valor_panel in enumerate(valores_panel):
            ax = axes[idx // ncols][idx % ncols]
            sub = sub_tipo[sub_tipo[col_panel] == valor_panel]

            _dibujar_lineas_por_razonador(ax, sub, metrica, col_x=col_x)

            if log_y:
                ax.set_yscale("log")
            else:
                ax.ticklabel_format(style="plain", axis="y", useOffset=False)
            valores_x = sorted(sub[col_x].unique())
            if valores_x:
                ax.set_xticks(valores_x)
            ax.set_title(f"{valor_panel} {etiqueta_panel}", fontsize=10)
            ax.grid(True, which="both", linestyle=":", alpha=0.4)

        for k in range(len(valores_panel), nrows * ncols):
            axes[k // ncols][k % ncols].axis("off")

        handles, labels = axes[0][0].get_legend_handles_labels()
        if handles:
            fig.legend(handles, labels, loc="upper center", ncol=3,
                       bbox_to_anchor=(0.5, 1.04), fontsize=8)
        fig.suptitle(f"{titulo_base} — {tipo}", y=1.08, fontsize=13)
        fig.text(0.5, -0.02, etiqueta_x, ha="center", fontsize=9)
        fig.text(-0.01, 0.5, ylabel, va="center", rotation="vertical", fontsize=9)
        fig.tight_layout()
        fig.savefig(carpeta_salida / f"{tipo}.png", dpi=150, bbox_inches="tight")
        plt.close(fig)


def graficar_pequenos_multiplos_por_tipo_mano(df, metrica, ylabel, titulo_base,
                                               carpeta_salida, log_y=True):
    """
    Genera un PNG por tipo de mano; cada uno con un subplot por cantidad de
    rangos (una grilla de pequeños múltiplos), graficando `metrica` vs palos.

    Pensada para instancias_divididas, donde cada tipo de mano tiene su
    propio CSV separado por cada combinación de rango x palo.
    """
    _graficar_pequenos_multiplos_por_tipo_mano(
        df, metrica, ylabel, titulo_base, carpeta_salida,
        col_panel="rangos", col_x="palos",
        etiqueta_panel="rangos", etiqueta_x="Cantidad de palos", log_y=log_y,
    )


def graficar_pequenos_multiplos_por_tipo_mano_vs_rangos(df, metrica, ylabel, titulo_base,
                                                         carpeta_salida, log_y=True):
    """
    Genera un PNG por tipo de mano; cada uno con un subplot por cantidad de
    palos (una grilla de pequeños múltiplos), graficando `metrica` vs
    rangos.

    Es el espejo de graficar_pequenos_multiplos_por_tipo_mano: mismo
    layout, pero con los roles de "palos" y "rangos" invertidos, para ver
    cómo escala cada razonador a medida que crece la cantidad de rangos
    (con la cantidad de palos fija), dentro de cada tipo de mano.
    """
    _graficar_pequenos_multiplos_por_tipo_mano(
        df, metrica, ylabel, titulo_base, carpeta_salida,
        col_panel="palos", col_x="rangos",
        etiqueta_panel="palos", etiqueta_x="Cantidad de rangos", log_y=log_y,
    )


def _graficar_pequenos_multiplos_por_razonador(df, metrica, ylabel, titulo_base,
                                                carpeta_salida, col_panel, col_x,
                                                etiqueta_panel, etiqueta_x, log_y=True):
    """
    Genera un PNG por cada razonador; cada uno con un subplot por cada
    valor de `col_panel` (grilla de pequeños múltiplos), graficando
    `metrica` vs `col_x` con una línea por tipo de mano dentro de cada
    subplot.

    Es el "transpuesto" de _graficar_pequenos_multiplos_por_tipo_mano: en
    vez de un PNG por tipo de mano con una línea por razonador, aquí se
    arma un PNG por razonador con una línea por tipo de mano, para ver de
    un vistazo en qué tipos de mano se concentra la lentitud de CADA
    razonador (por ejemplo JFact disparándose en escalera/full mientras el
    resto se mantiene plano), sin tener que comparar 10 PNG por separado.
    """
    carpeta_salida.mkdir(parents=True, exist_ok=True)
    tipos_presentes = [t for t in ORDEN_TIPOS_MANO
                       if t != "Todas" and t in df["tipo_mano"].unique()]
    valores_panel = sorted(df[col_panel].unique())
    if not tipos_presentes or not valores_panel:
        return

    cmap = plt.get_cmap("tab10")
    colores_tipo = {t: cmap(i % 10) for i, t in enumerate(tipos_presentes)}

    ncols = 3
    nrows = int(np.ceil(len(valores_panel) / ncols))

    for razonador in RAZONADORES:
        sub_r = df[df["razonador"] == razonador]
        if sub_r.empty:
            continue

        fig, axes = plt.subplots(nrows, ncols, figsize=(4.6 * ncols, 3.6 * nrows), squeeze=False)
        hubo_lineas = False

        for idx, valor_panel in enumerate(valores_panel):
            ax = axes[idx // ncols][idx % ncols]
            sub_panel = sub_r[sub_r[col_panel] == valor_panel]

            for tipo in tipos_presentes:
                datos = sub_panel[sub_panel["tipo_mano"] == tipo].sort_values(col_x)
                ok = datos[~datos["es_timeout"]]
                if ok.empty:
                    continue
                ax.plot(ok[col_x], ok[metrica], marker="o", markersize=4, linewidth=1.3,
                        label=tipo, color=colores_tipo[tipo])
                hubo_lineas = True

            if log_y:
                ax.set_yscale("log")
            else:
                ax.ticklabel_format(style="plain", axis="y", useOffset=False)
            valores_x = sorted(sub_panel[col_x].unique())
            if valores_x:
                ax.set_xticks(valores_x)
            ax.set_title(f"{valor_panel} {etiqueta_panel}", fontsize=10)
            ax.grid(True, which="both", linestyle=":", alpha=0.4)

        if not hubo_lineas:
            plt.close(fig)
            continue

        for k in range(len(valores_panel), nrows * ncols):
            axes[k // ncols][k % ncols].axis("off")

        handles, labels = [], []
        for ax_ in axes.flat:
            handles, labels = ax_.get_legend_handles_labels()
            if handles:
                break
        if handles:
            fig.legend(handles, labels, loc="upper center", ncol=5,
                       bbox_to_anchor=(0.5, 1.06), fontsize=8)
        fig.suptitle(f"{titulo_base} — {razonador}", y=1.1, fontsize=13)
        fig.text(0.5, -0.02, etiqueta_x, ha="center", fontsize=9)
        fig.text(-0.01, 0.5, ylabel, va="center", rotation="vertical", fontsize=9)
        fig.tight_layout()
        fig.savefig(carpeta_salida / f"{_slug_razonador(razonador)}.png", dpi=150, bbox_inches="tight")
        plt.close(fig)


def graficar_comparacion_tipos_mano_vs_palos(df, metrica, ylabel, titulo_base, carpeta_salida, log_y=False):
    """
    Genera un PNG por razonador, con un panel por cantidad de rangos y una
    línea por tipo de mano dentro de cada panel, graficando `metrica` vs
    cantidad de palos. Pensada para instancias_divididas.
    """
    _graficar_pequenos_multiplos_por_razonador(
        df, metrica, ylabel, titulo_base, carpeta_salida,
        col_panel="rangos", col_x="palos",
        etiqueta_panel="rangos", etiqueta_x="Cantidad de palos", log_y=log_y,
    )


def graficar_comparacion_tipos_mano_vs_rangos(df, metrica, ylabel, titulo_base, carpeta_salida, log_y=False):
    """
    Es el espejo de graficar_comparacion_tipos_mano_vs_palos: un PNG por
    razonador, con un panel por cantidad de palos y una línea por tipo de
    mano, graficando `metrica` vs cantidad de rangos.
    """
    _graficar_pequenos_multiplos_por_razonador(
        df, metrica, ylabel, titulo_base, carpeta_salida,
        col_panel="palos", col_x="rangos",
        etiqueta_panel="palos", etiqueta_x="Cantidad de rangos", log_y=log_y,
    )


def _graficar_heatmap_tipo_mano(df, carpeta_salida, metrica, cbar_label,
                                 fmt_tick, titulo_metrica, razonadores=None):
    """
    Función interna genérica: genera, por cada razonador en `razonadores`
    (por defecto todos, RAZONADORES), un heatmap tipo_mano x rangos ->
    `metrica`, con un panel por cantidad de palos.

    Compartida por graficar_heatmap_tipo_mano (metrica="total_s") y
    graficar_heatmap_tipo_mano_memoria (metrica="mem_pico_mb"), para no
    duplicar la lógica de armado de los paneles ni la normalización global
    de color.

    Pensada para instancias_divididas. Permite ver de un vistazo en qué
    tipos de mano y a qué escala se concentra el costo (tiempo o memoria)
    de cada razonador (por ejemplo JFact en escalera/full). La escala de
    color se normaliza de forma global, a partir de los valores válidos de
    TODOS los razonadores graficados en conjunto, para que los PNG
    resultantes (uno por razonador) compartan exactamente la misma barra de
    color y sean comparables entre sí (y no solo los paneles dentro de un
    mismo PNG).
    """
    carpeta_salida.mkdir(parents=True, exist_ok=True)
    razonadores = razonadores if razonadores is not None else RAZONADORES
    tipos_presentes = [t for t in ORDEN_TIPOS_MANO
                       if t != "Todas" and t in df["tipo_mano"].unique()]
    rangos_unicos = sorted(df["rangos"].unique())
    palos_unicos = sorted(df["palos"].unique())

    if not tipos_presentes or not rangos_unicos or not palos_unicos:
        return

    df_razonadores = df[df["razonador"].isin(razonadores)]
    valores_validos_global = df_razonadores.loc[~df_razonadores["es_timeout"], metrica].dropna()
    if not valores_validos_global.empty:
        vmin_global = valores_validos_global.min()
        vmax_global = valores_validos_global.max()
        norm_global = (mcolors.Normalize(vmin=vmin_global, vmax=vmax_global)
                       if vmax_global > vmin_global else None)
    else:
        norm_global = None

    for razonador in razonadores:
        sub_r = df[df["razonador"] == razonador]
        norm = norm_global

        fig, axes = plt.subplots(1, len(palos_unicos),
                                  figsize=(3.6 * len(palos_unicos) + 2, 0.55 * len(tipos_presentes) + 2.5),
                                  squeeze=False)
        axes = axes[0]
        im = None

        for k, palos in enumerate(palos_unicos):
            ax = axes[k]
            sub = sub_r[sub_r["palos"] == palos]
            matriz = np.full((len(tipos_presentes), len(rangos_unicos)), np.nan)
            es_to = np.zeros_like(matriz, dtype=bool)

            for i, tipo in enumerate(tipos_presentes):
                for j, rangos in enumerate(rangos_unicos):
                    fila = sub[(sub["tipo_mano"] == tipo) & (sub["rangos"] == rangos)]
                    if fila.empty:
                        continue
                    row = fila.iloc[0]
                    if row["es_timeout"]:
                        es_to[i, j] = True
                    else:
                        matriz[i, j] = row[metrica]

            im = ax.imshow(np.ma.masked_invalid(matriz), cmap="viridis", norm=norm, aspect="auto")

            for i in range(len(tipos_presentes)):
                for j in range(len(rangos_unicos)):
                    if es_to[i, j]:
                        ax.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False,
                                                    hatch="//", edgecolor="red", linewidth=1.2))
                        ax.text(j, i, "TO", ha="center", va="center", color="red",
                                fontsize=7, fontweight="bold")

            ax.set_xticks(range(len(rangos_unicos)))
            ax.set_xticklabels(rangos_unicos, rotation=45, fontsize=8)
            ax.set_yticks(range(len(tipos_presentes)))
            ax.set_yticklabels(tipos_presentes if k == 0 else [], fontsize=8)
            ax.set_xlabel("Rangos", fontsize=9)
            ax.set_title(f"{palos} palos", fontsize=10)

        fig.suptitle(f"{titulo_metrica} — {razonador}", fontsize=13)
        if im is not None:
            cbar = fig.colorbar(im, ax=axes.tolist(), label=cbar_label, shrink=0.85)
            cbar.ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_tick))
        fig.savefig(carpeta_salida / f"{_slug_razonador(razonador)}.png", dpi=150, bbox_inches="tight")
        plt.close(fig)


def graficar_heatmap_tipo_mano(df, carpeta_salida, razonadores=None):
    """
    Genera, por cada razonador (por defecto los tres), un heatmap tipo_mano
    x rangos -> tiempo (s), con un panel por cantidad de palos.

    Pensada para instancias_divididas. Ver _graficar_heatmap_tipo_mano para
    el detalle del manejo de timeouts y la normalización de color.
    """
    _graficar_heatmap_tipo_mano(
        df, carpeta_salida, metrica="total_s", cbar_label="Tiempo total (s)",
        fmt_tick=_formatear_tick_tiempo,
        titulo_metrica="Tiempo total por tipo de mano",
        razonadores=razonadores,
    )


def graficar_heatmap_tipo_mano_memoria(df, carpeta_salida, razonadores=None):
    """
    Genera, por cada razonador, un heatmap tipo_mano x rangos -> memoria
    peak (MB), con un panel por cantidad de palos.

    Es el equivalente en memoria de graficar_heatmap_tipo_mano. Por
    defecto se restringe a HermiT y JFact (Openllet queda casi siempre en
    TIMEOUT a estas escalas, por lo que un heatmap de memoria para él
    aportaría poco), pero se puede pasar `razonadores` explícitamente para
    incluir a los tres.
    """
    _graficar_heatmap_tipo_mano(
        df, carpeta_salida, metrica="mem_pico_mb", cbar_label="Memoria peak (MB)",
        fmt_tick=_formatear_tick_memoria,
        titulo_metrica="Memoria utilizada por tipo de mano",
        razonadores=razonadores if razonadores is not None else ["HermiT", "JFact (FaCT++)"],
    )


def _slug_razonador(razonador: str) -> str:
    """
    Devuelve la primera palabra del nombre de un razonador (por ejemplo
    "JFact" a partir de "JFact (FaCT++)"), usada como nombre de archivo PNG.
    """
    return razonador.split(" ")[0].replace("(", "").replace(")", "")

# =============================================================================
# Punto de entrada
# =============================================================================

def main():
    """
    Función principal. Lee los argumentos de línea de comandos, construye el
    DataFrame consolidado a partir de la carpeta de resultados y genera
    tanto el CSV resumen como todos los gráficos de instancias_completas e
    instancias_divididas en la carpeta de salida.
    """
    parser = argparse.ArgumentParser(
        description="Genera graficos a partir de los CSV de benchmark OWL en la carpeta 'resultados'.")
    parser.add_argument("--resultados", default="../resultados",
                         help="Carpeta raiz de resultados (por defecto ../resultados)")
    parser.add_argument("--salida", default=None,
                         help="Carpeta de salida para los graficos (por defecto <resultados>/graficos)")
    args = parser.parse_args()

    carpeta_resultados = Path(args.resultados).resolve()
    if not carpeta_resultados.exists():
        print(f"[ERROR] No existe la carpeta de resultados: {carpeta_resultados}")
        sys.exit(1)

    carpeta_graficos = Path(args.salida).resolve() if args.salida else carpeta_resultados / "graficos"
    carpeta_graficos.mkdir(parents=True, exist_ok=True)

    print(f"Leyendo CSV de benchmark desde: {carpeta_resultados}")
    df = construir_dataframe(carpeta_resultados)

    if df.empty:
        print("[ERROR] No se pudo construir ningun dato a partir de los CSV encontrados.")
        sys.exit(1)

    ruta_csv_global = carpeta_graficos / "resumen_metricas_global.csv"
    df.to_csv(ruta_csv_global, index=False, encoding="utf-8-sig")
    print(f"Resumen global guardado en: {ruta_csv_global}  ({len(df)} filas)")

    df_completas = df[df["tipo_instancias"] == "instancias_completas"]
    df_divididas = df[df["tipo_instancias"] == "instancias_divididas"]

    if not df_completas.empty:
        print(f"Generando graficos de instancias_completas... ({len(df_completas)} filas)")
        base = carpeta_graficos / "instancias_completas"
        graficar_metrica_vs_escala(
            df_completas, "total_s", "Tiempo total (s)",
            "Tiempo total de clasificacion", base / "tiempo_vs_palos", log_y=False)
        graficar_metrica_vs_escala(
            df_completas, "mem_pico_mb", "Memoria peak (MB)",
            "Memoria utilizada", base / "memoria_vs_palos", log_y=False)
        graficar_metrica_vs_rangos(
            df_completas, "total_s", "Tiempo total (s)",
            "Tiempo total de clasificacion", base / "tiempo_vs_rangos", log_y=False)
        graficar_metrica_vs_rangos(
            df_completas, "mem_pico_mb", "Memoria peak (MB)",
            "Memoria utilizada", base / "memoria_vs_rangos", log_y=False)
        graficar_heatmap_tiempo(df_completas, base / "heatmaps_tiempo")
        graficar_heatmap_memoria(df_completas, base / "heatmaps_memoria", razonadores=RAZONADORES)
        graficar_comparacion_barajas_vs_palos(
            df_completas, "total_s", "Tiempo total (s)",
            "Comparacion de barajas (tiempo)", base / "comparacion_barajas_tiempo_vs_palos")
        graficar_comparacion_barajas_vs_palos(
            df_completas, "mem_pico_mb", "Memoria peak (MB)",
            "Comparacion de barajas (memoria)", base / "comparacion_barajas_memoria_vs_palos")
        graficar_comparacion_barajas_vs_rangos(
            df_completas, "total_s", "Tiempo total (s)",
            "Comparacion de barajas (tiempo)", base / "comparacion_barajas_tiempo_vs_rangos")
        graficar_comparacion_barajas_vs_rangos(
            df_completas, "mem_pico_mb", "Memoria peak (MB)",
            "Comparacion de barajas (memoria)", base / "comparacion_barajas_memoria_vs_rangos")
    else:
        print("[!] No se encontraron datos de instancias_completas.")

    if not df_divididas.empty:
        print(f"Generando graficos de instancias_divididas... ({len(df_divididas)} filas)")
        base = carpeta_graficos / "instancias_divididas"
        graficar_pequenos_multiplos_por_tipo_mano(
            df_divididas, "total_s", "Tiempo total (s)",
            "Tiempo total de clasificacion", base / "tiempo_por_tipo_mano_vs_palos", log_y=False)
        graficar_pequenos_multiplos_por_tipo_mano(
            df_divididas, "mem_pico_mb", "Memoria peak (MB)",
            "Memoria utilizada", base / "memoria_por_tipo_mano_vs_palos", log_y=False)
        graficar_pequenos_multiplos_por_tipo_mano_vs_rangos(
            df_divididas, "total_s", "Tiempo total (s)",
            "Tiempo total de clasificacion", base / "tiempo_por_tipo_mano_vs_rangos", log_y=False)
        graficar_pequenos_multiplos_por_tipo_mano_vs_rangos(
            df_divididas, "mem_pico_mb", "Memoria peak (MB)",
            "Memoria utilizada", base / "memoria_por_tipo_mano_vs_rangos", log_y=False)
        graficar_heatmap_tipo_mano(df_divididas, base / "heatmaps_tiempo_por_tipo")
        graficar_heatmap_tipo_mano_memoria(df_divididas, base / "heatmaps_memoria_por_tipo", razonadores=RAZONADORES)
        graficar_comparacion_tipos_mano_vs_palos(
            df_divididas, "total_s", "Tiempo total (s)",
            "Comparacion de tipos de mano (tiempo)", base / "comparacion_tipos_mano_tiempo_vs_palos")
        graficar_comparacion_tipos_mano_vs_palos(
            df_divididas, "mem_pico_mb", "Memoria peak (MB)",
            "Comparacion de tipos de mano (memoria)", base / "comparacion_tipos_mano_memoria_vs_palos")
        graficar_comparacion_tipos_mano_vs_rangos(
            df_divididas, "total_s", "Tiempo total (s)",
            "Comparacion de tipos de mano (tiempo)", base / "comparacion_tipos_mano_tiempo_vs_rangos")
        graficar_comparacion_tipos_mano_vs_rangos(
            df_divididas, "mem_pico_mb", "Memoria peak (MB)",
            "Comparacion de tipos de mano (memoria)", base / "comparacion_tipos_mano_memoria_vs_rangos")
    else:
        print("[!] No se encontraron datos de instancias_divididas.")

    print("\nProceso terminado.")
    print(f"Graficos disponibles en: {carpeta_graficos}")


if __name__ == "__main__":
    main()