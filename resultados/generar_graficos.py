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
# Los casos TIMEOUT  nunca se representan con un valor de tiempo inventado, sino que
# se marcan visualmente con una X roja en los gráficos de línea, o con
# achurado rojo en los heatmaps, usando el umbral de timeout configurado del
# razonador solo como referencia visual.
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

TIMEOUT_SEGUNDOS = {
    "HermiT": 1800,
    "JFact (FaCT++)": 1800,
    "Openllet (Pellet)": 1800,
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

def _dibujar_lineas_por_razonador(ax, sub, metrica):
    """
    Dibuja sobre un eje ya creado una línea de `metrica` vs "palos" por cada
    razonador presente en sub (salvos los casos de TIMEOUT).
    """
    for razonador in RAZONADORES:
        datos_r = sub[sub["razonador"] == razonador].sort_values("palos")
        if datos_r.empty:
            continue
        color = COLOR_RAZONADOR.get(razonador)

        ok = datos_r[~datos_r["es_timeout"]]

        if not ok.empty:
            ax.plot(ok["palos"], ok[metrica], marker="o", label=razonador, color=color)


def graficar_metrica_vs_escala(df, metrica, ylabel, titulo_base, carpeta_salida, log_y=True):
    """
    Genera un PNG por cada cantidad de rangos presente en df, graficando
    `metrica` vs cantidad de palos, con una línea por razonador.

    Pensada para instancias_completas, donde cada combinación de rango x
    palo corresponde a un único CSV ("todas" las manos en un mismo archivo).
    """
    carpeta_salida.mkdir(parents=True, exist_ok=True)
    rangos_unicos = sorted(df["rangos"].unique())

    for rangos in rangos_unicos:
        sub = df[df["rangos"] == rangos]
        fig, ax = plt.subplots(figsize=(7, 5))

        _dibujar_lineas_por_razonador(ax, sub, metrica)

        if log_y:
            ax.set_yscale("log")
        else:
            ax.ticklabel_format(style="plain", axis="y", useOffset=False)
        palos_unicos = sorted(sub["palos"].unique())
        ax.set_xticks(palos_unicos)
        ax.set_xlabel("Cantidad de palos")
        ax.set_ylabel(ylabel)
        ax.set_title(f"{titulo_base} — {rangos} rangos")
        ax.grid(True, which="both", linestyle=":", alpha=0.5)
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(carpeta_salida / f"barajas_{rangos}_rangos.png", dpi=150)
        plt.close(fig)


def graficar_heatmap_tiempo(df, carpeta_salida):
    """
    Genera un heatmap rangos x palos -> tiempo total (s), uno por razonador.

    Pensada para instancias_completas. Los timeouts se muestran con achurado
    rojo y la etiqueta "TIMEOUT" en vez de un color de la escala, para no
    confundirlos nunca con un tiempo real medido.
    """
    carpeta_salida.mkdir(parents=True, exist_ok=True)
    rangos_unicos = sorted(df["rangos"].unique())
    palos_unicos = sorted(df["palos"].unique())

    for razonador in RAZONADORES:
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
                    matriz[i, j] = TIMEOUT_SEGUNDOS.get(razonador, np.nan)
                else:
                    matriz[i, j] = row["total_s"]

        _dibujar_heatmap_individual(
            matriz, es_to, rangos_unicos, palos_unicos,
            xlabel="Cantidad de palos", ylabel="Cantidad de rangos",
            titulo=f"Tiempo total de clasificacion — {razonador}",
            ruta_salida=carpeta_salida / f"{_slug_razonador(razonador)}.png",
        )


def _formatear_tick_tiempo(valor, pos=None):
    """
    Formatea un tick del colorbar de tiempo como número entero.
    """
    if valor >= 1:
        return f"{int(round(valor))}"
    return f"{valor:g}"


def _dibujar_heatmap_individual(matriz, es_to, etiquetas_y, etiquetas_x,
                                 xlabel, ylabel, titulo, ruta_salida):
    """
    Dibuja y guarda un único heatmap a partir de una matriz de tiempos (s) y
    una matriz booleana es_to que indica qué celdas corresponden a TIMEOUT.

    Usa escala de color lineal. Las celdas TIMEOUT se sobreescriben con
    achurado rojo y la etiqueta "TIMEOUT", en vez de dejar que participen de
    la escala.
    """
    fig, ax = plt.subplots(figsize=(1.1 * len(etiquetas_x) + 2, 0.9 * len(etiquetas_y) + 2))

    valores_validos = matriz[~np.isnan(matriz) & ~es_to]
    valores_to = matriz[~np.isnan(matriz) & es_to]
    todos_los_valores = np.concatenate([v for v in [valores_validos, valores_to] if v.size])

    if todos_los_valores.size:
        vmin = todos_los_valores.min()
        vmax = todos_los_valores.max()
        norm = mcolors.Normalize(vmin=vmin, vmax=vmax) if vmax > vmin else None
    else:
        norm = None

    im = ax.imshow(np.ma.masked_invalid(matriz), cmap="viridis", norm=norm, aspect="auto")

    for i in range(matriz.shape[0]):
        for j in range(matriz.shape[1]):
            if np.isnan(matriz[i, j]):
                continue
            if es_to[i, j]:
                ax.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False,
                                            hatch="//", edgecolor="red", linewidth=1.4))
                ax.text(j, i, "TIMEOUT", ha="center", va="center",
                        color="red", fontsize=7, fontweight="bold")
            else:
                ax.text(j, i, f"{matriz[i, j]:.2f}s", ha="center", va="center",
                        color="white", fontsize=8)

    ax.set_xticks(range(len(etiquetas_x)))
    ax.set_xticklabels(etiquetas_x)
    ax.set_yticks(range(len(etiquetas_y)))
    ax.set_yticklabels(etiquetas_y)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(titulo, fontsize=11)
    if todos_los_valores.size:
        cbar = fig.colorbar(im, ax=ax, label="Tiempo total (s)")
        cbar.ax.yaxis.set_major_formatter(mticker.FuncFormatter(_formatear_tick_tiempo))
    fig.tight_layout()
    fig.savefig(ruta_salida, dpi=150)
    plt.close(fig)


def graficar_pequenos_multiplos_por_tipo_mano(df, metrica, ylabel, titulo_base,
                                               carpeta_salida, log_y=True):
    """
    Genera un PNG por tipo de mano; cada uno con un subplot por cantidad de
    rangos (una grilla de pequeños múltiplos), graficando `metrica` vs palos.

    Pensada para instancias_divididas, donde cada tipo de mano tiene su
    propio CSV separado por cada combinación de rango x palo.
    """
    carpeta_salida.mkdir(parents=True, exist_ok=True)
    tipos_presentes = [t for t in ORDEN_TIPOS_MANO
                       if t != "Todas" and t in df["tipo_mano"].unique()]
    rangos_unicos = sorted(df["rangos"].unique())

    ncols = 3
    nrows = int(np.ceil(len(rangos_unicos) / ncols)) if rangos_unicos else 1

    for tipo in tipos_presentes:
        sub_tipo = df[df["tipo_mano"] == tipo]
        fig, axes = plt.subplots(nrows, ncols, figsize=(4.6 * ncols, 3.6 * nrows), squeeze=False)

        for idx, rangos in enumerate(rangos_unicos):
            ax = axes[idx // ncols][idx % ncols]
            sub = sub_tipo[sub_tipo["rangos"] == rangos]

            _dibujar_lineas_por_razonador(ax, sub, metrica)

            if log_y:
                ax.set_yscale("log")
            else:
                ax.ticklabel_format(style="plain", axis="y", useOffset=False)
            palos_unicos = sorted(sub["palos"].unique())
            if palos_unicos:
                ax.set_xticks(palos_unicos)
            ax.set_title(f"{rangos} rangos", fontsize=10)
            ax.grid(True, which="both", linestyle=":", alpha=0.4)

        for k in range(len(rangos_unicos), nrows * ncols):
            axes[k // ncols][k % ncols].axis("off")

        handles, labels = axes[0][0].get_legend_handles_labels()
        if handles:
            fig.legend(handles, labels, loc="upper center", ncol=3,
                       bbox_to_anchor=(0.5, 1.04), fontsize=8)
        fig.suptitle(f"{titulo_base} — {tipo}", y=1.08, fontsize=13)
        fig.text(0.5, -0.02, "Cantidad de palos", ha="center", fontsize=9)
        fig.text(-0.01, 0.5, ylabel, va="center", rotation="vertical", fontsize=9)
        fig.tight_layout()
        fig.savefig(carpeta_salida / f"{tipo}.png", dpi=150, bbox_inches="tight")
        plt.close(fig)


def graficar_heatmap_tipo_mano(df, carpeta_salida):
    """
    Genera, por cada razonador, un heatmap tipo_mano x rangos -> tiempo (s),
    con un panel por cantidad de palos.

    Pensada para instancias_divididas. Permite ver de un vistazo en qué
    tipos de mano y a qué escala se concentra la lentitud de cada razonador
    (por ejemplo JFact en escalera/full). La escala de color se normaliza
    por razonador (no por panel) para que los paneles de un mismo razonador
    sean comparables entre sí.
    """
    carpeta_salida.mkdir(parents=True, exist_ok=True)
    tipos_presentes = [t for t in ORDEN_TIPOS_MANO
                       if t != "Todas" and t in df["tipo_mano"].unique()]
    rangos_unicos = sorted(df["rangos"].unique())
    palos_unicos = sorted(df["palos"].unique())

    if not tipos_presentes or not rangos_unicos or not palos_unicos:
        return

    for razonador in RAZONADORES:
        sub_r = df[df["razonador"] == razonador]

        valores_validos = sub_r.loc[~sub_r["es_timeout"], "total_s"].dropna()
        vmax_to = TIMEOUT_SEGUNDOS.get(razonador, None)
        candidatos_vmax = [v for v in [valores_validos.max() if not valores_validos.empty else None,
                                        vmax_to] if v is not None]
        vmax = max(candidatos_vmax) if candidatos_vmax else 1.0
        vmin = valores_validos.min() if not valores_validos.empty else 0.0
        norm = mcolors.Normalize(vmin=vmin, vmax=vmax) if vmax > vmin else None

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
                        matriz[i, j] = TIMEOUT_SEGUNDOS.get(razonador, np.nan)
                    else:
                        matriz[i, j] = row["total_s"]

            im = ax.imshow(np.ma.masked_invalid(matriz), cmap="viridis", norm=norm, aspect="auto")

            for i in range(len(tipos_presentes)):
                for j in range(len(rangos_unicos)):
                    if np.isnan(matriz[i, j]):
                        continue
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

        fig.suptitle(f"Tiempo total por tipo de mano — {razonador}", fontsize=13)
        if im is not None:
            cbar = fig.colorbar(im, ax=axes.tolist(), label="Tiempo total (s)", shrink=0.85)
            cbar.ax.yaxis.set_major_formatter(mticker.FuncFormatter(_formatear_tick_tiempo))
        fig.savefig(carpeta_salida / f"{_slug_razonador(razonador)}.png", dpi=150, bbox_inches="tight")
        plt.close(fig)


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
            "Tiempo total de clasificacion", base / "tiempo_vs_escala", log_y=False)
        graficar_metrica_vs_escala(
            df_completas, "mem_pico_mb", "Memoria pico (MB)",
            "Memoria pico utilizada", base / "memoria_vs_escala", log_y=False)
        graficar_heatmap_tiempo(df_completas, base / "heatmaps_tiempo")
    else:
        print("[!] No se encontraron datos de instancias_completas.")

    if not df_divididas.empty:
        print(f"Generando graficos de instancias_divididas... ({len(df_divididas)} filas)")
        base = carpeta_graficos / "instancias_divididas"
        graficar_pequenos_multiplos_por_tipo_mano(
            df_divididas, "total_s", "Tiempo total (s)",
            "Tiempo total de clasificacion", base / "tiempo_por_tipo_mano", log_y=False)
        graficar_pequenos_multiplos_por_tipo_mano(
            df_divididas, "mem_pico_mb", "Memoria pico (MB)",
            "Memoria pico utilizada", base / "memoria_por_tipo_mano", log_y=False)
        graficar_heatmap_tipo_mano(df_divididas, base / "heatmaps_tiempo_por_tipo")
    else:
        print("[!] No se encontraron datos de instancias_divididas.")

    print("\nProceso terminado.")
    print(f"Graficos disponibles en: {carpeta_graficos}")


if __name__ == "__main__":
    main()