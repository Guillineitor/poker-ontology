import os
from owlready2 import *

def main():
    print("==================================================")
    print(" Razonador de Póker - Python (owlready2)")
    print("==================================================")
    
    # 1. Configurar los paths para que owlready2 encuentre los imports
    onto_path.append("../ontologia")
    onto_path.append("../clasificadores")
    onto_path.append("../experimentos")
    
    # 2. Cargar las ontologías
    print("Cargando ontología base...")
    base = get_ontology("../ontologia/ontologia_base_poker.ttl").load()
    
    print("Cargando clasificador (Color)...")
    clf_color = get_ontology("../clasificadores/clasificador_06_color.ttl").load()
    
    print("Cargando instancias de prueba...")
    instancias = get_ontology("../experimentos/instancias_prueba_poker.ttl").load()
    
    print("\nOntologías cargadas. Iniciando razonador (HermiT)...")
    
    # 3. Ejecutar el razonador sobre las instancias
    with instancias:
        # sync_reasoner ejecuta HermiT por defecto en owlready2
        sync_reasoner(infer_property_values=True)
    
    print("Razonamiento finalizado.\n")
    print("Resultados de Clasificación:")
    print("--------------------------------------------------")
    
    # 4. Consultar resultados
    # Obtenemos la clase MejorMano de la ontología base
    MejorMano = base.search_one(iri="*MejorMano")
    
    if not MejorMano:
        print("[!] No se encontró la clase MejorMano.")
        return

    # Iterar sobre las instancias que el razonador identificó como de tipo MejorMano
    for ind in base.get_instances_of(MejorMano):
        # Filtrar clases inferidas, excluyendo las generales como 'Thing' o 'MejorMano'
        clases_especificas = [
            c.name for c in ind.INDIRECT_is_a 
            if hasattr(c, "name") and c.name not in ["MejorMano", "Thing"]
        ]
        
        # Eliminar duplicados si los hay
        clases_especificas = list(set(clases_especificas))
        
        clases_str = ", ".join(f"[{c}]" for c in clases_especificas) if clases_especificas else "(Sin clasificación específica)"
        
        print(f"Instancia : {ind.name}")
        print(f"Inferencia: {clases_str}\n")


if __name__ == "__main__":
    # Asegurarnos de correr desde el directorio es/razonamiento
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    main()
