# Generador de ontologías de baraja

Generador de ontologías con barajas de cartas customizadas en OWL 2 DL, serializado en sintaxis Turtle (`.ttl`). Consta de dos scripts:

- **`generador_ontologias.py`** : genera una ontología individual.
- **`generar_ontologias.ps1`** : automatiza `generador_ontologias.py` para producir de una sola vez todo el catálogo de ontologías usado en el benchmark, organizándolas en subcarpetas.

---

## Contenido

- Descripción general
- Generación de ontologías
- Organización del código
- Uso
  - Generación individual 
  - Generación múltiple 
- Observaciones importantes

---

## Descripción general

| Atributo | Valor |
|---|---|
| Entrada | Nombre, palos y rangos definidos por el usuario |
| Salida | Archivo(s) `.ttl` en OWL 2 DL |
| Perfil OWL | OWL 2 DL |
| Serialización | Turtle (`.ttl`) |
| Script principal | `generador_ontologias.py` |
| Script de generación múltiple | `generar_ontologias.ps1` |

El generador construye una ontología completa para una baraja definida por el usuario. La IRI base y el nombre del archivo de salida se derivan automáticamente del nombre de la baraja, por lo que el usuario solo necesita indicar nombre, palos y rangos. El sistema mantiene la estructura de la ontología base de póker y adapta únicamente los datos propios de cada baraja.

Para el benchmark, en vez de ejecutar `generador_ontologias.py` manualmente una vez por cada combinación de palos y rangos, se usa `generar_ontologias.ps1`, que llama al generador por cada combinación de la matriz de pruebas y organiza los archivos resultantes automáticamente (para generar ontologías de forma más cómoda).

---

## Generación de ontologías

El generador produce una ontología con los siguientes componentes:

| Componente | Descripción |
|---|---|
| IRI base y metadatos | Derivados automáticamente del nombre de la baraja |
| Palos y rangos | Clases cerradas con `owl:oneOf` |
| Cartas | Combinación de un palo y un rango |
| Mano | Manos de cinco cartas |
| Clasificadores de mano | Solo los tipos de mano posibles según cantidad de palos, rangos y cartas |
| Individuos ABox | Individuos concretos de cartas y axiomas `owl:AllDifferent` |

---

## Organización del código

### `generador_ontologias.py`

El archivo está dividido en cuatro bloques:

| Bloque | Funcionalidad |
|---|---|
| Helpers de nombre | Normalizan texto libre a identificadores Turtle seguros y etiquetas legibles |
| Bloques de ontología | Generan secciones TBox y ABox reutilizables |
| Clasificadores de manos | Emiten las restricciones OWL para cada jugada |
| Interfaz interactiva | Solicita datos por consola y escribe el archivo `.ttl` final |

La función `generar_ontologia()` es el punto de ensamblaje. Recibe el nombre de la baraja, la IRI base, los palos y los rangos ya validados, y devuelve el contenido Turtle completo. Los clasificadores de manos se incluyen únicamente cuando la cantidad de palos, rangos y cartas permite formarlos con la baraja indicada.

### `generar_ontologias.ps1`

Es un script de para generar una tanda de ontología de una sola vez, dados los palos y rangos posibles.

| Bloque | Funcionalidad |
|---|---|
| Parámetros | `ScriptGenerador`, `CarpetaSalida`, `PythonExe`, `GruposRangos`, `GruposPalos`, `SoloListar` |
| Catálogo fijo | Listas de `$todosPalos` y `$todosRangos`, de donde se usan para las combinaciones pedidas |
| Bucle de combinaciones | Por cada cantidad de rangos y de palos que exista, se arma el nombre de la baraja (`baraja_<N>r_<M>p`) y envía las respuestas a `generador_ontologias.py`
| Organización de salida | Mueve cada `.ttl` generado a una subcarpeta `barajas_<N>_rangos/` dentro de `CarpetaSalida` |

Como `generador_ontologias.py` siempre escribe en `<raíz_proyecto>\ontologias\ontologias_customizadas\`, `-CarpetaSalida` debe apuntar a esa misma carpeta para que el script pueda mover los archivos generados.

---

## Uso

### Generación individual 

```powershell
python generador_ontologias.py
```

El script solicita de forma interactiva el nombre de la baraja, sus palos y sus rangos. Al ejecutarse, muestra la IRI base generada y un resumen con los totales de palos, rangos y cartas antes de escribir el archivo.

El archivo generado se guarda en:

```text
ontologias/ontologias_customizadas/<nombre_ontología>.ttl
```

Este modo es útil para generar una baraja puntual o para probar palos/rangos fuera del catálogo del benchmark. La organización de ese archivo dentro de `ontologias_customizadas/` queda a criterio del usuario.

### Generación múltiple

```powershell
.\generar_ontologias.ps1
```

Con los valores usados para el benchmark, genera las 24 ontologías del catálogo de este mismo: 6 grupos de rangos (6, 13, 19, 25, 31, 37) × 4 grupos de palos (4, 8, 12, 16). Cada combinación usa como nombre `baraja_<N>r_<M>p` (por ejemplo, `baraja_6r_8p` para 6 rangos y 8 palos) y los palos/rangos se toman en orden desde el catálogo fijo del script.

Parámetros disponibles:

| Parámetro | Descripción | Valor por defecto |
|---|---|---|
| `-ScriptGenerador` | Ruta a `generador_ontologias.py` | `.\generador_ontologias.py` |
| `-CarpetaSalida` | Carpeta `ontologias_customizadas` donde escribe el generador y donde se crean las subcarpetas `barajas_<N>_rangos` | `..\ontologias\ontologias_customizadas` |
| `-PythonExe` | Ejecutable de Python a usar | `python` |
| `-GruposRangos` | Cantidades de rangos a generar (una subcarpeta por valor) | `6,13,19,25,31,37` |
| `-GruposPalos` | Cantidades de palos a generar dentro de cada grupo de rangos | `4,8,12,16` |
| `-SoloListar` | Solo imprime las combinaciones que se generarían, sin ejecutar el generador ni tocar el disco | (desactivado) |

Más información en la documentación de **`generar_ontologias.ps1`**.

---

## Observaciones importantes

### Orden de los rangos

Los rangos deben ingresarse de menor a mayor valor. Esa posición se usa para calcular las ventanas de rangos consecutivos que definen la Escalera y la Escalera Real. En el catálogo del script **`generar_ontologias.ps1`**, este orden ya viene dado por la lista fija de rangos.

### Mínimo de rangos 

Si la baraja tiene menos de cinco rangos, el generador omite `Escalera`, `Color`, `EscaleraColor` y `EscaleraReal` porque no es posible formar ventanas de cinco cartas consecutivas. `EscaleraReal` requiere al menos seis rangos, ya que necesita una ventana de cinco más al menos un rango inferior que la diferencie de la única secuencia posible.

### Mínimo de palos para manos de grupo

Si la baraja tiene menos de cuatro palos, el generador omite las manos que exigen varias cartas del mismo rango. `Par` y `DoblePar` requieren al menos dos palos,
`Trio` y `Full` requieren al menos tres, y `Poker` requiere al menos cuatro, ya que en una baraja solo existe una carta por combinación de palo y rango, por
lo que el número de palos fija el máximo de cartas repetibles dentro de un mismo rango.

### Manos posibles según la baraja

El generador evalúa la cantidad de palos y rangos antes de emitir clasificadores. Una mano que exige varias cartas del mismo rango solo se genera si existen suficientes palos:

| Mano | Condición mínima |
|---|---|
| `CartaAlta` | al menos 5 cartas en total |
| `Par` | al menos 2 palos |
| `DoblePar` | al menos 2 palos y 2 rangos |
| `Trio` | al menos 3 palos |
| `Full` | al menos 3 palos y 2 rangos |
| `Poker` | al menos 4 palos |
| `Escalera`, `Color`, `EscaleraColor` | al menos 5 rangos |
| `EscaleraReal` | al menos 6 rangos |

Si una clase no se genera, el archivo `.ttl` incluye un comentario con el motivo de la omisión. El árbol de jerarquía de manos en el encabezado de la ontología también refleja únicamente las clases efectivamente generadas.

Para que todos los experimentos del benchmark probaran la misma cantidad de tipos de mano de póker, el catálogo se definió a partir de un mínimo de 4 palos y 6 rangos. De ahí las valores y cantidades presentes de palos y rangos.

### Cierre de la clase `Carta`

`Carta` no se cierra con `owl:oneOf`, sino que sus restricciones del dominio quedan acotadas indirectamente por el cierre de `Palo` y `Rango` a través de las propiedades funcionales `tienePalo` y `tieneRango`. Esto fue decidido para simplificar un poco la ontología. Este cierre impide que un razonador infiera la existencia de cartas adicionales no declaradas, ya que bajo la Open World Assumption nada lo prohíbe sin intervención explícita, pero sin sobreexplotar a los razonadores.

### `owl:AllDifferent` para palos, rangos y cartas

OWL 2 DL no asume distinción entre individuos por defecto: la Unique Name Assumption no aplica. Sin declaraciones explícitas de unicidad, el razonador podría unificar individuos que el modelador considera distintos. Por eso el generador emite tres bloques `owl:AllDifferent`: uno para los palos, otro para los rangos y uno para las cartas.

### Propiedad auxiliar `manoTienePar` en `DoblePar`

`DoblePar` depende de la propiedad auxiliar `manoTienePar`. Para clasificar manos concretas, el ABox debe indicar manualmente qué rangos forman par en cada mano. Esta decisión sigue el mismo patrón que la ontología base de póker: en OWL 2 DL no es posible expresar directamente «dos rangos distintos, cada uno con al menos 2 cartas», usando solo `contieneCarta` y cardinalidades calificadas, por lo que esa responsabilidad se delega al ABox, para así no complejizar más la ontología de lo que se requiere en el benchmark. `Full` se define como la intersección de `Trio` y `DoblePar`, por lo que también tiene esta propiedad.