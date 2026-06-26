# Generador de instancias de manos de póker

Generador automático de un ABox en formato Turtle (`.ttl`) con 40 manos de póker aleatorias, cuatro por cada uno de los diez tipos de mano del Texas Hold'em. El script es `generador_instancias.py`.

---

## Contenido

- Descripción general
- Generación de instancias
- Organización del código
- Uso
- Observaciones importantes

---

## Descripción general

| Atributo | Valor |
|---|---|
| Entrada | Ruta a un archivo `.ttl` de ontología de baraja |
| Salida | Archivo ABox `.ttl` con 40 manos de póker |
| Manos por tipo | 4 |
| Tipos de mano | 10 (desde Carta Alta hasta Escalera Real) |
| Script principal | `generador_instancias.py` |

El generador lee una ontología de baraja producida por `generador_ontologias.py` y extrae dinámicamente de ella los rangos, los palos y las cartas disponibles. Con esa información construye manos válidas para cada tipo, las serializa en Turtle y escribe el archivo de salida en la misma carpeta del script. Al adaptarse a la baraja de entrada, funciona con cualquier configuración de palos y rangos, no solo con la baraja inglesa de 52 cartas.

---

## Generación de instancias

El generador produce un único archivo ABox con los siguientes componentes:

| Componente | Descripción |
|---|---|
| Prefijos Turtle | Uno por tipo de mano más los prefijos de la ontología base |
| Declaración de ontología | Metadatos e `owl:imports` apuntando a la ontología de baraja de entrada |
| Bloques de manos | 4 individuos `poker:Mano` por cada uno de los 10 tipos |
| Labels descriptivos | `rdfs:label` en lenguaje natural con el detalle de cada mano |
| `manoTienePar` | Propiedad auxiliar incluida en las manos de Doble Par y Full |
| `owl:AllDifferent` | Una declaración por tipo de mano para garantizar la unicidad de los individuos |

---

## Organización del código

El archivo está dividido en cinco bloques:

| Bloque | Responsabilidad |
|---|---|
| Lectura de la ontología | Extrae rangos, palos, etiquetas y cartas del archivo `.ttl` de entrada |
| Generadores de manos | Una función por tipo de mano; producen combinaciones válidas y aleatorias |
| Construcción de bloques TTL | Serializa cada mano, su label y su bloque `owl:AllDifferent` en Turtle |
| Generación del archivo completo | Ensambla todas las secciones y escribe el archivo de salida |
| Punto de entrada | Valida el argumento de consola e invoca la función principal |

La función `generar_archivo()` es el punto de ensamblaje. Recibe la ruta a la ontología, delega la lectura a `leer_ontologia()`, invoca cada generador de mano el número de veces configurado y concatena los bloques resultantes en el archivo final.

---

## Uso

```powershell
python generador_instancias.py ../(carpeta donde se ubica la ontología)/<nombre_ontología>.ttl
```

**Ejemplo:**

```powershell
python generador_instancias.py ..\ontologias\ontologias_customizadas\baraja_6r_4p.ttl
```

El archivo generado se guarda en la misma carpeta del script, con el nombre:

```text
instancias_<nombre_ontología>.ttl
```

Durante la ejecución, el script imprime en consola el resumen de la baraja leída y el label de cada mano generada, lo que permite verificar el resultado sin abrir el archivo.

Posteriormente el usuario puede organizar las ontologías creadas de la manera que prefiera. En el caso de las instancias de las ontologías para el benchmark, se reorganizó en distintas subcarpetas dentro de la carpeta instancias/, una por cada cantidad de rangos.

---

## Observaciones importantes

### Compatibilidad con la ontología de entrada

El script espera que la ontología de entrada siga la estructura producida por `generador_ontologias.py`: individuos de tipo `poker:Palo`, `poker:Rango` y `poker:Carta`, con las propiedades `poker:tienePalo` y `poker:tieneRango` declaradas en el ABox. Si alguna de esas estructuras falta o está malformada, el script lanza un error descriptivo antes de generar ninguna mano. Considerar también que evidentemente se requiere tener la ontología ya creada antes de poder generar instancias de esta con el script.

### Orden de los rangos

Los rangos se extraen en el orden en que aparecen declarados en la ontología de entrada. Ese orden determina qué secuencias son consecutivas para la Escalera y cuáles son los cinco rangos más altos para la Escalera Real. Por eso es importante que la ontología de origen haya sido generada con los rangos en orden de menor a mayor valor.

### Manos posibles según la baraja

El script verifica qué tipos de mano pueden formarse con la baraja de entrada antes de intentar generarlos. Las mismas condiciones mínimas que aplica `generador_ontologias.py` al emitir clasificadores son las que determinan si un generador de instancias tiene sentido ejecutar:

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

### Propiedad `manoTienePar` en Doble Par y Full

Las manos de Doble Par y Full incluyen la propiedad auxiliar `poker:manoTienePar` apuntando a los rangos que forman par en esa mano. Esto es necesario porque el clasificador `DoblePar` de la ontología depende de esa propiedad para reconocer la mano bajo el razonador, y `Full` se define como la intersección de `Trio` y `DoblePar`, por lo que tiene 
esta propiedad.

### Escalera Real y variedad de palos

El generador de Escalera Real intenta que las cuatro instancias del tipo no repitan el mismo palo. Para ello lleva un registro de los palos ya utilizados en generaciones anteriores y prioriza los que aún no han aparecido. Si la baraja tiene un único palo con los cinco rangos más altos disponibles, las cuatro instancias usarán ese palo y el archivo resultará válido igualmente (para el benchmark no se considera estos casos, pero está la opción para cualquier usuario).
