# Proyecto de Trabajo de Título: Ontología y Benchmark del Póker

Este proyecto está estructurado de acuerdo a las fases del Trabajo de Título, con el objetivo de desarrollar un benchmark de póker para evaluar razonadores OWL.

## Estructura del Proyecto


* **`base_ontology/`**: Diseño en OWL de las entidades principales del juego de Póker (cartas, palos, valores, manos) y jugadas estándar.
* **`experiments/`**: Definición y ejecución de experimentos, variando parámetros del dominio y definiendo configuraciones.
* **`ontology_generator/`**: Componente que a partir de la ontología base crea variantes automáticas controladas.
* **`reasoning_tasks/`**: Definición de las tareas a resolver (clasificación de manos, comparación para ganadora, verificación de consistencia).
* **`results_analysis/`**: Análisis e interpretación de datos, evaluación de escalabilidad y tendencias.
