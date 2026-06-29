# Generador de ontologías de baraja

Generador de ontologías con barajas de cartas customizadas en OWL 2 DL, serializado en sintaxis Turtle (`.ttl`). El script es `generador_ontologias.py`.

---

## Contenido

- Descripción general
- Generación de ontologías
- Organización del código
- Uso
- Observaciones importantes

---

## Descripción general

| Atributo | Valor |
|---|---|
| Entrada | Nombre, palos y rangos definidos por el usuario |
| Salida | Archivo `.ttl` en OWL 2 DL |
| Perfil OWL | OWL 2 DL |
| Serialización | Turtle (`.ttl`) |
| Script principal | `generador_ontologias.py` |

El generador construye una ontología completa para una baraja definida por el usuario. La IRI base y el nombre del archivo de salida se derivan automáticamente del nombre de la baraja, por lo que el usuario solo necesita indicar nombre, palos y rangos. El sistema mantiene la estructura de la ontología base de póker y adapta únicamente los datos propios de cada baraja.

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

El archivo está dividido en cuatro bloques:

| Bloque | Funcionalidad |
|---|---|
| Helpers de nombre | Normalizan texto libre a identificadores Turtle seguros y etiquetas legibles |
| Bloques de ontología | Generan secciones TBox y ABox reutilizables |
| Clasificadores de manos | Emiten las restricciones OWL para cada jugada |
| Interfaz interactiva | Solicita datos por consola y escribe el archivo `.ttl` final |

La función `generar_ontologia()` es el punto de ensamblaje. Recibe el nombre de la baraja, la IRI base, los palos y los rangos ya validados, y devuelve el contenido Turtle completo. Los clasificadores de manos se incluyen únicamente cuando la cantidad de palos, rangos y cartas permite formarlos con la baraja indicada.

---

## Uso

```powershell
python generador_ontologias.py
```

El script solicita de forma interactiva el nombre de la baraja, sus palos y sus rangos. Al ejecutarse, muestra la IRI base generada y un resumen con los totales de palos, rangos y cartas antes de escribir el archivo.

El archivo generado se guarda en:

```text
ontologias/ontologias_customizadas/<nombre_ontología>.ttl
```

Posteriormente el usuario puede organizar las ontologías creadas de la manera que prefiera. En el caso de las ontologías para el benchmark, se reorganizó en distintas subcarpetas dentro de la carpeta ontologias/ontologias_customizadas/, una por cada cantidad de rangos.

---

## Observaciones importantes

### Orden de los rangos

Los rangos deben ingresarse de menor a mayor valor. Esa posición se usa para para calcular las ventanas de rangos consecutivos que definen la Escalera y la Escalera Real.

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

Para el desarrollo del benchmark, solamente se creó ontologías desde los 4 palos y 6 rangos, para poder probar los clasificadores con la misma cantidad de 
tipo manos de póker en todos los experimentos.

### Cierre de la clase `Carta`

`Carta` no se cierra con `owl:oneOf`, sino que sus restricciones del dominio quedan acotadas indirectamente por el cierre de `Palo` y `Rango` a través de las propiedades funcionales `tienePalo` y `tieneRango`. Esto fue decidido para simplificar un poco la ontología. Este cierre impide que un razonador infiera la existencia de cartas adicionales no declaradas, ya que bajo la Open World Assumption nada lo prohíbe sin intervención explícita, pero sin sobreexplotar a los razonadores.

### `owl:AllDifferent` para palos, rangos y cartas

OWL 2 DL no asume distinción entre individuos por defecto: la Unique Name Assumption no aplica. Sin declaraciones explícitas de unicidad, el razonador podría unificar individuos que el modelador considera distintos. Por eso el generador emite tres bloques `owl:AllDifferent`: uno para los palos, otro para los rangos y uno para las cartas.

### Propiedad auxiliar `manoTienePar` en `DoblePar`

`DoblePar` depende de la propiedad auxiliar `manoTienePar`. Para clasificar manos concretas, el ABox debe indicar manualmente qué rangos forman par en cada mano. Esta decisión sigue el mismo patrón que la ontología base de póker: en OWL 2 DL no es posible expresar directamente «dos rangos distintos, cada uno con al menos 2 cartas», usando solo `contieneCarta` y cardinalidades calificadas, por lo que esa responsabilidad se delega al ABox, para así no complejizar más la ontología de lo que se requiere en el benchmark. `Full` se define como la intersección de `Trio` y `DoblePar`, por lo que también tiene esta propiedad.
