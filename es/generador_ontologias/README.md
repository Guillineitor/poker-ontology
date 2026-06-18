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
| Cartas | Combinaciones de palo y rango |
| Mano | Mano de cinco cartas |
| Clasificadores de mano | CartaAlta, Par, DoblePar, Trio, Escalera, Color, Full, Poker, EscaleraColor y EscaleraReal |
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

### Propiedad *shortcut* `manoTienePar` en DoblePar

`DoblePar` depende de la propiedad auxiliar `manoTienePar`. Para clasificar manos concretas, el ABox de instancias debe indicar manualmente qué rangos forman par en cada mano. Esta decisión sigue el mismo patrón que la ontología base de póker: en OWL 2 DL no es posible expresar directamente "dos rangos distintos, cada uno con al menos 2 cartas" usando solo `contieneCarta` y cardinalidades calificadas, por lo que se delega al ABox.
