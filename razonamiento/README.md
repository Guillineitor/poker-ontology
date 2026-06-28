# Benchmark de Razonadores OWL — Ontología de Póker

Módulo Java para comparar los razonadores OWL **HermiT**, **Openllet (Pellet)** y **JFact (FaCT++)** sobre ontologías de póker con distintas variantes de barajas de cartas.

## Estructura

```
razonamiento/
├── src/main/java/poker/
│   ├── BenchmarkOWL.java               # Benchmark original (primeras pruebas)
│   ├── BenchmarkOWLDefinitivo.java        # Benchmark (resultados de experimentos)
│   └── TestViabilidadRazonadoresOWL.java  # Benchmark con timeout de 60 min (para verificar funcionamiento de los razonadores OWL)
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

### `BenchmarkOWL` — sin límite de tiempo

Ejecuta los tres razonadores sin restricción de tiempo. Clase principal del JAR.

### `BenchmarkOWLTimeout` — timeout de 10 minutos

HermiT corre sin límite. Openllet y JFact se cancelan si no terminan en 10 minutos.

### `TestViabilidadRazonadoresOWL` — timeout de 60 minutos

Igual que el anterior pero con un límite de 60 minutos por razonador.

---

## Ejecución

Todos los comandos se ejecutan desde la carpeta `razonamiento/`.

La sintaxis general es:

```
java [opciones_memoria] -jar|-cp <jar> [clase] <ontologia.ttl> <instancias.ttl>
```

Se recomienda asignar memoria adicional para ontologías grandes:

```powershell
java -Xms2g -Xmx4g -jar target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar <ontologia.ttl> <instancias.ttl>
```

---

## Comandos por ontología

### Ontología base (13 rangos)

```powershell
# BenchmarkOWL
java -jar target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar `
  ..\ontologias\ontologia_base\ontologia_base_poker.ttl `
  ..\instancias\instancias_ontologia_base_poker\instancias_poker_base.ttl

# BenchmarkOWLTimeout (10 min)
java -cp target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar poker.BenchmarkOWLTimeout `
  ..\ontologias\ontologia_base\ontologia_base_poker.ttl `
  ..\instancias\instancias_ontologia_base_poker\instancias_poker_base.ttl

# TestViabilidadRazonadoresOWL (60 min)
java -cp target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar poker.TestViabilidadRazonadoresOWL `
  ..\ontologias\ontologia_base\ontologia_base_poker.ttl `
  ..\instancias\instancias_ontologia_base_poker\instancias_poker_base.ttl
```

---

### Barajas de 6 rangos

```powershell
# 6 rangos / 4 palos
java -jar target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar `
  ..\ontologias\ontologias_customizadas\barajas_6_rangos\baraja_6r_4p.ttl `
  ..\instancias\instancias_barajas_6_rangos\instancias_baraja_6r_4p.ttl

# 6 rangos / 8 palos
java -jar target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar `
  ..\ontologias\ontologias_customizadas\barajas_6_rangos\baraja_6r_8p.ttl `
  ..\instancias\instancias_barajas_6_rangos\instancias_baraja_6r_8p.ttl

# 6 rangos / 12 palos
java -jar target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar `
  ..\ontologias\ontologias_customizadas\barajas_6_rangos\baraja_6r_12p.ttl `
  ..\instancias\instancias_barajas_6_rangos\instancias_baraja_6r_12p.ttl

# 6 rangos / 16 palos
java -jar target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar `
  ..\ontologias\ontologias_customizadas\barajas_6_rangos\baraja_6r_16p.ttl `
  ..\instancias\instancias_barajas_6_rangos\instancias_baraja_6r_16p.ttl
```

---

### Barajas de 13 rangos

```powershell
# Reemplazar Xr_Yp por la combinación deseada, por ejemplo 13r_4p, 13r_8p, etc.
java -jar target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar `
  ..\ontologias\ontologias_customizadas\barajas_13_rangos\baraja_Xr_Yp.ttl `
  ..\instancias\instancias_barajas_13_rangos\instancias_baraja_Xr_Yp.ttl
```

---

### Barajas de 19 rangos

```powershell
java -jar target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar `
  ..\ontologias\ontologias_customizadas\barajas_19_rangos\baraja_Xr_Yp.ttl `
  ..\instancias\instancias_barajas_19_rangos\instancias_baraja_Xr_Yp.ttl
```

---

### Barajas de 25 rangos

```powershell
java -jar target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar `
  ..\ontologias\ontologias_customizadas\barajas_25_rangos\baraja_Xr_Yp.ttl `
  ..\instancias\instancias_barajas_25_rangos\instancias_baraja_Xr_Yp.ttl
```

---

### Barajas de 31 rangos

```powershell
java -jar target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar `
  ..\ontologias\ontologias_customizadas\barajas_31_rangos\baraja_Xr_Yp.ttl `
  ..\instancias\instancias_barajas_31_rangos\instancias_baraja_Xr_Yp.ttl
```

---

### Barajas de 37 rangos

```powershell
java -jar target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar `
  ..\ontologias\ontologias_customizadas\barajas_37_rangos\baraja_Xr_Yp.ttl `
  ..\instancias\instancias_barajas_37_rangos\instancias_baraja_Xr_Yp.ttl
```

---

## Resultados

Cada ejecución genera dos archivos CSV en `resultados/`:

| Archivo | Contenido |
|---|---|
| `resumen_<timestamp>.csv` | Una fila por razonador con todas las métricas numéricas |
| `clasificacion_<timestamp>.csv` | Una fila por (razonador, individuo, clase inferida) |

Los archivos generados por `BenchmarkOWLTimeout` y `TestViabilidadRazonadoresOWL` usan el prefijo `resumen_timeout_` y `clasificacion_timeout_` respectivamente, para distinguirlos de los del benchmark sin límite.

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