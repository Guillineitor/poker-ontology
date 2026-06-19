# Generador de ontologías de baraja

Generador interactivo de ontologías de baraja en OWL 2 DL, serializado en sintaxis Turtle (`.ttl`). El script principal es `generador_ontologias.py`.

---

## Contenido

- Descripción general
- Qué genera
- Cómo se organiza el código
- Uso
- Supuestos importantes

---

## Descripción general

| Atributo | Valor |
|---|---|
| Entrada | Nombre, IRI, palos y rangos definidos por el usuario |
| Salida | Archivo `.ttl` en OWL 2 DL |
| Perfil OWL | OWL 2 DL |
| Serialización | Turtle (`.ttl`) |
| Script principal | `generador_ontologias.py` |

El generador construye una ontología completa para una baraja definida por el usuario. Mantiene la estructura de la ontología base de póker y cambia solo los datos propios de la baraja.

---

## Qué genera

El generador produce una ontología con los siguientes componentes:

| Componente | Descripción |
|---|---|
| IRI base y metadatos | Configurables por el usuario |
| Palos y rangos | Clases cerradas con `owl:oneOf` |
| Cartas | Clase cerrada con una carta por combinación de palo y rango |
| Mano | Mano de cinco cartas |
| Clasificadores de mano | Solo las clases de mano posibles según cantidad de palos, rangos y cartas |
| Individuos ABox | Individuos concretos y axiomas `owl:AllDifferent` |

---

## Cómo se organiza el código

El archivo está dividido en cuatro bloques:

| Bloque | Responsabilidad |
|---|---|
| Helpers de nombre | Normalizan texto libre a identificadores Turtle seguros y etiquetas legibles |
| Bloques de ontología | Generan secciones TBox/ABox reutilizables |
| Clasificadores de manos | Emiten las restricciones OWL para cada jugada |
| Interfaz interactiva | Pide datos por consola y escribe el `.ttl` final |

La función `generar_ontologia()` es el punto de ensamblaje. Recibe nombre, IRI, palos y rangos ya validados, y devuelve el contenido Turtle completo.

---

## Uso

```powershell
python generador_ontologias.py
```

El archivo generado se guarda en:

```text
es/ontologias/ontologias_customizadas/<nombre_baraja>.ttl
```

---

## Supuestos importantes

### Orden de los rangos

Los rangos deben ingresarse de menor a mayor valor. Esa posición se usa para asignar `tieneValorRango` y para calcular Escalera y EscaleraReal.

### Mínimo de rangos para escaleras

Si la baraja tiene menos de cinco rangos, el generador omite `Escalera`, `EscaleraColor` y `EscaleraReal` porque no puede formar ventanas de cinco cartas consecutivas.

### Manos posibles según la baraja

El generador evalúa la cantidad de palos y rangos antes de emitir clasificadores. Una mano que exige varias cartas del mismo rango solo se genera si existen suficientes palos:

| Mano | Condición mínima |
|---|---|
| `Par` | al menos 2 palos |
| `DoblePar` | al menos 2 palos y 2 rangos |
| `Trio` | al menos 3 palos |
| `Full` | al menos 3 palos y 2 rangos |
| `Poker` | al menos 4 palos |
| `Escalera`, `Color`, `EscaleraColor`, `EscaleraReal` | al menos 5 rangos |

Si una clase no se genera, el `.ttl` incluye un comentario con el motivo.

### Cierre de la clase Carta

`Carta` también se cierra con `owl:oneOf`, enumerando todas las cartas de la baraja. Esto impide que un razonador cree cartas anónimas adicionales con el mismo palo y rango bajo la Open World Assumption.

### Propiedad *shortcut* `manoTienePar` en DoblePar

`DoblePar` depende de la propiedad auxiliar `manoTienePar`. Para clasificar manos concretas, el ABox de instancias debe indicar manualmente qué rangos forman par en cada mano. Esta decisión sigue el mismo patrón que la ontología base de póker: en OWL 2 DL no es posible expresar directamente "dos rangos distintos, cada uno con al menos 2 cartas" usando solo `contieneCarta` y cardinalidades calificadas, por lo que se delega al ABox.
