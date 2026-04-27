package poker;

import org.semanticweb.owlapi.apibinding.OWLManager;
import org.semanticweb.owlapi.model.*;
import org.semanticweb.owlapi.reasoner.*;
import org.semanticweb.HermiT.ReasonerFactory;

import java.io.File;

public class InferenciaOWL {
    public static void main(String[] args) {
        try {
            OWLOntologyManager manager = OWLManager.createOWLOntologyManager();
            
            // Ajustar rutas relativas al lugar de ejecución (desde java-owlapi)
            File baseFile = new File("../../ontologia/ontologia_base_poker.ttl");
            File classFile = new File("../../clasificadores/clasificador_06_color.ttl");
            // Usamos las instancias de prueba que tienes generadas
            File instFile = new File("../../experimentos/instancias_prueba_poker.ttl");
            
            System.out.println("Cargando ontologías...");
            OWLOntology baseOntology = manager.loadOntologyFromOntologyDocument(baseFile);
            System.out.println("- Base cargada: " + baseOntology.getOntologyID().getOntologyIRI().orElse(null));
            
            OWLOntology classOntology = manager.loadOntologyFromOntologyDocument(classFile);
            System.out.println("- Clasificador cargado.");
            
            OWLOntology instOntology = manager.loadOntologyFromOntologyDocument(instFile);
            System.out.println("- Instancias cargadas.");
            
            // Combinar todo en una sola ontología para razonar correctamente (OWL API)
            System.out.println("\nCombinando ontologías...");
            OWLOntology mergedOntology = manager.createOntology(IRI.create("http://www.poker-ontology.org/merged"));
            manager.addAxioms(mergedOntology, baseOntology.getAxioms());
            manager.addAxioms(mergedOntology, classOntology.getAxioms());
            manager.addAxioms(mergedOntology, instOntology.getAxioms());
            
            System.out.println("Ontologías combinadas con éxito.\n");
            
            // Configurar el razonador HermiT
            System.out.println("Iniciando razonador HermiT...");
            OWLReasonerFactory reasonerFactory = new ReasonerFactory();
            ConsoleProgressMonitor progressMonitor = new ConsoleProgressMonitor();
            OWLReasonerConfiguration config = new SimpleConfiguration(progressMonitor);
            
            OWLReasoner reasoner = reasonerFactory.createReasoner(mergedOntology, config);
            
            // Sincronizar el razonador y verificar consistencia
            reasoner.precomputeInferences(InferenceType.CLASS_HIERARCHY, InferenceType.CLASS_ASSERTIONS);
            
            if (!reasoner.isConsistent()) {
                System.out.println("\n[!] La ontología es INCONSISTENTE. Revisa las definiciones.");
                return;
            }
            System.out.println("\n[✓] La ontología es CONSISTENTE.");
            System.out.println("==================================================");
            
            // IRI de las clases principales
            String baseIRI = "http://www.poker-ontology.org/poker#";
            OWLDataFactory factory = manager.getOWLDataFactory();
            OWLClass mejorManoClass = factory.getOWLClass(IRI.create(baseIRI + "MejorMano"));
            
            // Obtener todas las instancias de MejorMano
            NodeSet<OWLNamedIndividual> instances = reasoner.getInstances(mejorManoClass, false);
            System.out.println("Instancias de MejorMano encontradas: " + instances.getFlattened().size());
            System.out.println("--------------------------------------------------");
            
            // Iterar y mostrar sus clases inferidas
            for (OWLNamedIndividual ind : instances.getFlattened()) {
                System.out.println("Instancia: " + ind.getIRI().getShortForm());
                NodeSet<OWLClass> types = reasoner.getTypes(ind, true); // true = clases directas más específicas
                
                System.out.print("  Inferencia(s): ");
                boolean foundSpecificClass = false;
                for (OWLClass c : types.getFlattened()) {
                    String className = c.getIRI().getShortForm();
                    // Omitir clases base genéricas
                    if (!c.isOWLThing() && !className.equals("MejorMano")) {
                        System.out.print("[" + className + "] ");
                        foundSpecificClass = true;
                    }
                }
                if (!foundSpecificClass) {
                    System.out.print("(No pudo ser clasificada en una mano específica)");
                }
                System.out.println("\n");
            }
            
            // Liberar memoria
            reasoner.dispose();
            System.out.println("Razonamiento finalizado.");
            
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
