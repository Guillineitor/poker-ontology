# Proyecto de Trabajo de Título: Ontología y Benchmark del Póker

Este proyecto está estructurado de acuerdo a las fases del Trabajo de Título, con el objetivo de desarrollar un Benchmark de razonadores OWL 2 DL sobre un dominio de póker Texas Hold'em. El proyecto construye una ontología en OWL 2 DL que modela aspecto básicos del juego, genera instancias de manos de forma controlada y evalúa el rendimiento de múltiples razonadores sobre tareas de clasificación y consistencia.

---

## Contenido

- Descripción general
- Estructura del repositorio
- Módulos principales
  - `generador_ontologias/`
  - `instancias/`
  - `ontologias/`
  - `razonamiento/`
  - `resultados/`
- Razonadores evaluados
- Cómo ejecutar el benchmark

---

## Descripción general

| Atributo | Valor |
|---|---|
| Dominio | Póker Texas Hold'em |
| Perfil OWL | OWL 2 DL |
| Serialización | Turtle (`.ttl`) |
| API de razonamiento | OWL API 5.x |
| Idioma de la ontología | Español |
| Lenguaje del benchmark | Java 11, Maven |
| Lenguaje de los scripts | Python 3.14.3 (junto con librerías estándar) |

El proyecto evalúa la capacidad de razonadores OWL 2 DL para clasificar manos de póker (Par, Trío, Escalera, etc.) a partir de una ontología con restricciones de cardinalidad calificada y clases equivalentes. Se miden tiempos de inicialización, precomputación y memoria heap consumida.

---

## Estructura del repositorio

```
POKER-ONTOLOGY/
    ├── generador_ontologias/          # Generador automático de variantes de ontología
    ├── instancias/                    # ABox con instancias de manos de póker
    ├── ontologias/                    # TBox y variantes de la ontología
    │   ├── ontologia_base/            # Ontología base de pokér con baraja inglesa, en OWL 2 DL
    │   └── ontologias_customizadas/   # Variantes generadas para los experimentos
    ├── razonamiento/                  # Código del benchmark 
    ├── resultados/                    # Resultados del benchmark 
    └── README.md                      # Este archivo
```

---

## Módulos principales

### `generador_ontologias/`

Contiene un script de Python que toma la ontología base y genera variantes controladas modificando parámetros del dominio (número de palos y número de rangos). Las variantes se escriben en `ontologias/ontologias_customizadas/`.

Consultar `generador_ontologias/README.md` para detalles de configuración y parámetros disponibles.

### `instancias/`

Archivos Turtle (`.ttl`) con la ABox de cada experimento. Cada subcarpeta corresponde a una configuración distinta de instancias generadas sobre su respectiva ontología de
póker personalizada. Las instancias se producen con el script `generador_instancias.py`, que vive en esta misma carpeta y acepta como argumento la ruta a una ontología `.ttl`.

Para la ontología base de póker, las instancias están conformadas por:

| Tipo | Cantidad base | Descripción |
|---|---|---|
| `Palo` | 4 | Picas, Corazones, Diamantes, Tréboles |
| `Rango` | 13 | Dos a As |
| `Carta` | 52 | 13 rangos × 4 palos |
| `Mano` | 10 | 4 instancias de 5 cartas clasificadas por tipo |

En caso de ontologías de póker personalizadas usadas en este trabajo, la cantidad de palos, rangos y cartas cambia, pero la cantidad de instancias por cada mano sigue siendo 4.

### `ontologias/`

Contiene la TBox del dominio, dividida en:

- **`ontologia_base/`** — Ontología canónica con todas las clases (`Carta`, `Mano`, tipos de mano), propiedades de objeto y datos, y los 69 individuos fijos de la baraja. Serializada en Turtle, perfil OWL 2 DL.
- **`ontologias_customizadas/`** — Variantes generadas automáticamente por `generador_ontologias.py`, usadas en los experimentos de escalabilidad.

### `razonamiento/`

Proyecto Maven con el benchmark en Java. Compara razonadores sobre la ontología fusionada (TBox + ABox) y reporta métricas por razonador.

Métricas capturadas:

| Métrica | Descripción |
|---|---|
| Tiempo de inicialización | Tiempo en crear la instancia del razonador (ms) |
| Tiempo de precomputación | Tiempo en computar la jerarquía de clases (ms) |
| Tiempo total | Suma de los anteriores (ms) |
| Memoria heap | Incremento de memoria durante el razonamiento (MB) |
| Consistencia | Si la ontología es lógicamente consistente |
| Clases inferidas | Número de clases en la jerarquía inferida |
| Instancias por clase | Manos clasificadas en cada tipo (Par, Trío, etc.) |
| Inferencias totales | Suma de todas las aserciones de clase inferidas |

### `resultados/`

Salidas generadas tras ejecutar el benchmark: tablas comparativas en texto, logs de clasificación individual por instancia y archivos de resumen para análisis posterior.

---

## Razonadores evaluados

| Razonador | Artefacto Maven | Versión | 
|---|---|---|
| **HermiT** | `net.sourceforge.owlapi:org.semanticweb.hermit` | 1.4.3.517 | 
| **Openllet** | `com.github.galigator.openllet:openllet-owlapi` | 2.6.5 | 
| **JFact** | `net.sourceforge.owlapi:jfact` | 5.0.3 

Razonadores **excluidos** del benchmark:

| Razonador | Motivo de exclusión |
|---|---|
| ELK | Solo OWL 2 EL; no soporta cardinalidades calificadas ni `owl:hasValue` |

---

## Cómo ejecutar el benchmark

El flujo completo tiene tres etapas: generar las ontologías customizadas, generar las instancias correspondientes y finalmente correr el benchmark. Las dos primeras etapas son opcionales si se trabaja únicamente con la ontología base.

**Prerrequisitos:** Python 3.14.3+, Java 11+, Maven 3.6+. Los scripts de Python no requieren instalar dependencias externas, solo se usa librerías estándar.

---

### Etapa 1 — Generar ontologías customizadas

Este paso solo es necesario si se quieren experimentos con barajas distintas a la estándar (variedad en cantidad de palos o rangos).

```powershell
cd generador_ontologias/
python generador_ontologias.py
```

El script solicita de forma interactiva el nombre de la baraja, los palos y los rangos. La ontología resultante se escribe automáticamente en `ontologias/ontologias_customizadas/`. En este repositorio se creó y se organizó a mano las ontologías de acuerdo a la cantidad de rangos en distintas carpetas dentro de `ontologias/ontologias_customizadas/`. En `generador_ontologias/README.md` para más detalles sobre los parámetros disponibles para crear ontologías de póker personalizadas.

---

### Etapa 2 — Generar instancias

Una vez disponible la ontología, se pueden generar las instancias ABox correspondientes. El script debe ejecutarse desde la carpeta `instancias/` y recibe como argumento la ruta a la ontología `.ttl`.

```powershell
cd instancias/
python generador_instancias.py ../(carpeta donde se ubica la ontología)/<nombre_baraja>.ttl
```

El archivo de salida se genera en la misma carpeta `instancias/`, con un nombre derivado de la ontología de entrada.

---

### Etapa 3 — Ejecutar el benchmark Java

```powershell
cd razonamiento/
mvn clean package
java -jar target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar
```

El programa carga automáticamente `../ontologias/ontologia_base/` y `../instancias/instancias.ttl`, fusiona los axiomas en una sola ontología y ejecuta el benchmark para los tres razonadores en secuencia. Los resultados se imprimen en consola y se guardan en `resultados/`.