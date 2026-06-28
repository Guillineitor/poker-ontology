# Benchmark de Razonadores OWL — Ontología de Póker

Módulo Java para comparar los razonadores OWL **HermiT**, **Openllet (Pellet)** y **JFact (FaCT++)** sobre ontologías de póker con distintas variantes de barajas de cartas.

## Estructura

```
razonamiento/
├── src/main/java/poker/
│   ├── BenchmarkOWL.java                  # Benchmark original (primeras pruebas).
│   ├── TestViabilidadRazonadoresOWL.java  # Test para verificar funcionamiento de los razonadores OWL.
│   └── BenchmarkOWLDefinitivo.java        # Benchmark (resultados de experimentos).
└── pom.xml
```

## Requisitos

- Java 11 o superior.
- Maven 3.6 o superior.

## Compilación

Desde la carpeta `razonamiento/`:

```powershell
mvn clean package
```

Esto genera el JAR con todas las dependencias en:

```
target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar
```

---

## Archivos de benchmark

### `BenchmarkOWL`

Ejecuta los tres razonadores uno por uno, dado una ontología de póker y un archivo con instancias de manos dado esa ontología.
Fue el primer experimento para hacer primeras pruebas con los razonadores. Se descubrió aquí que los razonadores OpenPellet y JFact no daban resultados, 
incluso después de muchas horas de ejecución, a diferencia de HermiT que si terminaba.

### `TestViabilidadRazonadoresOWL` 

Igual que el anterior pero con un límite temporal de 60 minutos de ejecución para los razonadores OpenPellet y JFact. Este experimento fue hecho para 
comprobar que los razonadores OpenPellet y JFact no son efectivos frente a una ontología compleja y con una influyente combinatoria en sus instancias como
lo es una ontología de póker, incluso teniendo solo 4 instancias de manos para que infiera los razonadores. HermiT corre sin límite temporal.

### `BenchmarkOWLDefinitivo` 

Benchmark definitivo. HermiT corre sin límite. Openllet y JFact se cancelan si no terminan en 5 minutos (Solo para la muestra de resultados, aunque esos razonadores
no sean efectivos).

---

## Ejecución

Todos los comandos se ejecutan desde la carpeta `razonamiento/`.

La sintaxis general es:

```
java [opciones_memoria_RAM] -jar|-cp <jar> [clase] <ontologia.ttl> <instancias.ttl>
```

Se recomienda asignar memoria RAM inicial alta para estos experimentos, para mayor rápidez frente a ontologías de póker con más axiomas. Ejemplo:

```powershell
java -Xms28g -Xmx30g -jar target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar <ontologia.ttl> <instancias.ttl>
```

---

## Comandos usados en los experimentos

### Pruebas con Ontología de Póker Base (13 rangos y 4 palo)

```powershell
# BenchmarkOWL
java -Xms28g -Xmx30g -jar target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar `
  ..\ontologias\ontologia_base\ontologia_base_poker.ttl `
  ..\instancias\instancias_ontologia_base_poker\instancias_poker_base.ttl

# TestViabilidadRazonadoresOWL 
java -Xms28g -Xmx30g -cp target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar poker.TestViabilidadRazonadoresOWL `
  ..\ontologias\ontologia_base\ontologia_base_poker.ttl `
  ..\instancias\instancias_ontologia_base_poker\instancias_poker_base_reducida.ttl

# BenchmarkOWLDefinitivo 
java -Xms28g -Xmx30g -cp target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar poker.BenchmarkOWLDefinitivo  `
  ..\ontologias\ontologia_base\ontologia_base_poker.ttl `
  ..\instancias\instancias_ontologia_base_poker\instancias_poker_base.ttl

```

---

### Pruebas con Ontología Customizadas de Póker 

#### Barajas de 6 rangos

```powershell
# 6 rangos / 4 palos
java -Xms28g -Xmx30g -cp target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar poker.BenchmarkOWLDefinitivo `
  ..\ontologias\ontologias_customizadas\barajas_6_rangos\baraja_6r_4p.ttl `
  ..\instancias\instancias_barajas_6_rangos\instancias_baraja_6r_4p.ttl

# 6 rangos / 8 palos
java -Xms28g -Xmx30g -cp target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar poker.BenchmarkOWLDefinitivo `
  ..\ontologias\ontologias_customizadas\barajas_6_rangos\baraja_6r_8p.ttl `
  ..\instancias\instancias_barajas_6_rangos\instancias_baraja_6r_8p.ttl

# 6 rangos / 12 palos
java -Xms28g -Xmx30g -cp target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar poker.BenchmarkOWLDefinitivo `
  ..\ontologias\ontologias_customizadas\barajas_6_rangos\baraja_6r_12p.ttl `
  ..\instancias\instancias_barajas_6_rangos\instancias_baraja_6r_12p.ttl

# 6 rangos / 16 palos
java -Xms28g -Xmx30g -cp target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar poker.BenchmarkOWLDefinitivo `
  ..\ontologias\ontologias_customizadas\barajas_6_rangos\baraja_6r_16p.ttl `
  ..\instancias\instancias_barajas_6_rangos\instancias_baraja_6r_16p.ttl
```

---

#### Barajas de 13 rangos

```powershell
# 13 rangos / 4 palos
java -Xms28g -Xmx30g -cp target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar poker.BenchmarkOWLDefinitivo `
  ..\ontologias\ontologias_customizadas\barajas_13_rangos\baraja_13r_4p.ttl `
  ..\instancias\instancias_barajas_13_rangos\instancias_baraja_13r_4p.ttl

# 13 rangos / 8 palos
java -Xms28g -Xmx30g -cp target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar poker.BenchmarkOWLDefinitivo `
  ..\ontologias\ontologias_customizadas\barajas_13_rangos\baraja_13r_8p.ttl `
  ..\instancias\instancias_barajas_13_rangos\instancias_baraja_13r_8p.ttl

# 13 rangos / 12 palos
java -Xms28g -Xmx30g -cp target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar poker.BenchmarkOWLDefinitivo `
  ..\ontologias\ontologias_customizadas\barajas_13_rangos\baraja_13r_12p.ttl `
  ..\instancias\instancias_barajas_13_rangos\instancias_baraja_13r_12p.ttl

# 13 rangos / 16 palos
java -Xms28g -Xmx30g -cp target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar poker.BenchmarkOWLDefinitivo `
  ..\ontologias\ontologias_customizadas\barajas_13_rangos\baraja_13r_16p.ttl `
  ..\instancias\instancias_barajas_13_rangos\instancias_baraja_13r_16p.ttl
```

---

#### Barajas de 19 rangos

```powershell
# 19 rangos / 4 palos
java -Xms28g -Xmx30g -cp target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar poker.BenchmarkOWLDefinitivo `
  ..\ontologias\ontologias_customizadas\barajas_19_rangos\baraja_19r_4p.ttl `
  ..\instancias\instancias_barajas_19_rangos\instancias_baraja_19r_4p.ttl

# 19 rangos / 8 palos
java -Xms28g -Xmx30g -cp target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar poker.BenchmarkOWLDefinitivo `
  ..\ontologias\ontologias_customizadas\barajas_19_rangos\baraja_19r_8p.ttl `
  ..\instancias\instancias_barajas_19_rangos\instancias_baraja_19r_8p.ttl

# 19 rangos / 12 palos
java -Xms28g -Xmx30g -cp target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar poker.BenchmarkOWLDefinitivo `
  ..\ontologias\ontologias_customizadas\barajas_19_rangos\baraja_19r_12p.ttl `
  ..\instancias\instancias_barajas_19_rangos\instancias_baraja_19r_12p.ttl

# 19 rangos / 16 palos
java -Xms28g -Xmx30g -cp target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar poker.BenchmarkOWLDefinitivo `
  ..\ontologias\ontologias_customizadas\barajas_19_rangos\baraja_19r_16p.ttl `
  ..\instancias\instancias_barajas_19_rangos\instancias_baraja_19r_16p.ttl
```

---

#### Barajas de 25 rangos

```powershell
# 25 rangos / 4 palos
java -Xms28g -Xmx30g -cp target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar poker.BenchmarkOWLDefinitivo `
  ..\ontologias\ontologias_customizadas\barajas_25_rangos\baraja_25r_4p.ttl `
  ..\instancias\instancias_barajas_25_rangos\instancias_baraja_25r_4p.ttl

# 25 rangos / 8 palos
java -Xms28g -Xmx30g -cp target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar poker.BenchmarkOWLDefinitivo `
  ..\ontologias\ontologias_customizadas\barajas_25_rangos\baraja_25r_8p.ttl `
  ..\instancias\instancias_barajas_25_rangos\instancias_baraja_25r_8p.ttl

# 25 rangos / 12 palos
java -Xms28g -Xmx30g -cp target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar poker.BenchmarkOWLDefinitivo `
  ..\ontologias\ontologias_customizadas\barajas_25_rangos\baraja_25r_12p.ttl `
  ..\instancias\instancias_barajas_25_rangos\instancias_baraja_25r_12p.ttl

# 25 rangos / 16 palos
java -Xms28g -Xmx30g -cp target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar poker.BenchmarkOWLDefinitivo `
  ..\ontologias\ontologias_customizadas\barajas_25_rangos\baraja_25r_16p.ttl `
  ..\instancias\instancias_barajas_25_rangos\instancias_baraja_25r_16p.ttl
```

---

#### Barajas de 31 rangos

```powershell
# 31 rangos / 4 palos
java -Xms28g -Xmx30g -cp target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar poker.BenchmarkOWLDefinitivo `
  ..\ontologias\ontologias_customizadas\barajas_31_rangos\baraja_31r_4p.ttl `
  ..\instancias\instancias_barajas_31_rangos\instancias_baraja_31r_4p.ttl

# 31 rangos / 8 palos
java -Xms28g -Xmx30g -cp target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar poker.BenchmarkOWLDefinitivo `
  ..\ontologias\ontologias_customizadas\barajas_31_rangos\baraja_31r_8p.ttl `
  ..\instancias\instancias_barajas_31_rangos\instancias_baraja_31r_8p.ttl

# 31 rangos / 12 palos
java -Xms28g -Xmx30g -cp target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar poker.BenchmarkOWLDefinitivo `
  ..\ontologias\ontologias_customizadas\barajas_31_rangos\baraja_31r_12p.ttl `
  ..\instancias\instancias_barajas_31_rangos\instancias_baraja_31r_12p.ttl

# 31 rangos / 16 palos
java -Xms28g -Xmx30g -cp target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar poker.BenchmarkOWLDefinitivo `
  ..\ontologias\ontologias_customizadas\barajas_31_rangos\baraja_31r_16p.ttl `
  ..\instancias\instancias_barajas_31_rangos\instancias_baraja_31r_16p.ttl
```

---

#### Barajas de 37 rangos

```powershell
# 37 rangos / 4 palos
java -Xms28g -Xmx30g -cp target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar poker.BenchmarkOWLDefinitivo `
  ..\ontologias\ontologias_customizadas\barajas_37_rangos\baraja_37r_4p.ttl `
  ..\instancias\instancias_barajas_37_rangos\instancias_baraja_37r_4p.ttl

# 37 rangos / 8 palos
java -Xms28g -Xmx30g -cp target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar poker.BenchmarkOWLDefinitivo `
  ..\ontologias\ontologias_customizadas\barajas_37_rangos\baraja_37r_8p.ttl `
  ..\instancias\instancias_barajas_37_rangos\instancias_baraja_37r_8p.ttl

# 37 rangos / 12 palos
java -Xms28g -Xmx30g -cp target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar poker.BenchmarkOWLDefinitivo `
  ..\ontologias\ontologias_customizadas\barajas_37_rangos\baraja_37r_12p.ttl `
  ..\instancias\instancias_barajas_37_rangos\instancias_baraja_37r_12p.ttl

# 37 rangos / 16 palos
java -Xms28g -Xmx30g -cp target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar poker.BenchmarkOWLDefinitivo `
  ..\ontologias\ontologias_customizadas\barajas_37_rangos\baraja_37r_16p.ttl `
  ..\instancias\instancias_barajas_37_rangos\instancias_baraja_37r_16p.ttl
```

---

## Resultados

Cada ejecución genera dos archivos CSV en `resultados/`:

| Archivo | Contenido |
|---|---|
| `resumen_<timestamp>.csv` | Una fila por razonador con todas las métricas numéricas |
| `clasificacion_<timestamp>.csv` | Una fila por (razonador, individuo, clase inferida) |

### Métricas del resumen

| Columna | Descripción |
|---|---|
| `variante` | Nombre del archivo de ontología (sin extensión) |
| `razonador` | Nombre del razonador |
| `carga_ms` | Tiempo de lectura del TTL desde disco (ms) |
| `init_ms` | Tiempo de creación del razonador (ms) |
| `precomp_ms` | Tiempo de precomputación de inferencias (ms) |
| `total_ms` | Suma de los tres anteriores (ms) |
| `mem_antes_mb` | Heap usada antes de la precomputación (MB) |
| `mem_despues_mb` | Heap usada después de la precomputación (MB) |
| `mem_delta_mb` | Diferencia de heap (MB) |
| `consistente` | Si la ontología es consistente según el razonador |
| `clases_jerarquia` | Número de clases en la jerarquía inferida |
| `total_inferencias` | Total de individuos clasificados sumando todas las clases |
| `inst_<Clase>` | Individuos clasificados bajo cada clase de mano |