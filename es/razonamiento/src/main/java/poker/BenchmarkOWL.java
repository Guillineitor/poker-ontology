package poker;

import org.semanticweb.owlapi.apibinding.OWLManager;
import org.semanticweb.owlapi.model.*;
import org.semanticweb.owlapi.reasoner.*;

// HermiT
import org.semanticweb.HermiT.ReasonerFactory;

// Openllet (Pellet)
import openllet.owlapi.OpenlletReasonerFactory;

// JFact (FaCT++)
import uk.ac.manchester.cs.jfact.JFactFactory;

import java.io.File;
import java.lang.management.ManagementFactory;
import java.lang.management.MemoryMXBean;
import java.util.*;

/**
 * BenchmarkOWL — compara HermiT, Openllet (Pellet) y JFact (FaCT++)
 * sobre la ontología de póker.
 *
 * Métricas por razonador:
 *   • Tiempo de carga + inicialización   (ms)
 *   • Tiempo de precomputación           (ms)
 *   • Tiempo total de clasificación      (ms)
 *   • Memoria heap usada antes/después   (MB)
 *   • Consistencia de la ontología
 *   • Número de clases en la jerarquía inferida
 *   • Número de instancias clasificadas  (por clase de mano)
 *   • Número total de inferencias        (aserciones de clase inferidas)
 */
public class BenchmarkOWL {

    // ── Rutas relativas desde razonamiento/ ─────────────────────────────────
    private static final String BASE_TTL  = "../ontologia/ontologia_base_poker.ttl";

    // Los 10 archivos de instancias en ../instancias/
    private static final String[] INST_TTLS = {
        "../instancias/instancias_carta_alta.ttl",
        "../instancias/instancias_par.ttl",
        "../instancias/instancias_doble_par.ttl",
        "../instancias/instancias_trio.ttl",
        "../instancias/instancias_escalera.ttl",
        "../instancias/instancias_color.ttl",
        "../instancias/instancias_fullhouse.ttl",
        "../instancias/instancias_poker.ttl",
        "../instancias/instancias_escalera_color.ttl",
        "../instancias/instancias_escalera_real.ttl"
    };

    private static final String BASE_IRI  = "http://www.poker-ontology.org/poker#";

    // Clases de mano que queremos consultar
    private static final String[] CLASES_MANO = {
        "CartaAlta", "Par", "DoblePar", "Trio",
        "Escalera", "Color", "FullHouse", "Poker", "EscaleraColor", "EscaleraReal"
    };

    // ── Colores ANSI para la terminal ────────────────────────────────────────
    private static final String RESET  = "\u001B[0m";
    private static final String BOLD   = "\u001B[1m";
    private static final String CYAN   = "\u001B[36m";
    private static final String GREEN  = "\u001B[32m";
    private static final String RED    = "\u001B[31m";
    private static final String YELLOW = "\u001B[33m";

    public static void main(String[] args) throws Exception {

        banner();

        // 1. Cargar y combinar ontologías (una sola vez, compartida)
        OWLOntology merged = cargarOntologias();

        // 2. Definir razonadores a comparar
        List<EntradaRazonador> razonadores = Arrays.asList(
            new EntradaRazonador("HermiT",          new ReasonerFactory()),
            new EntradaRazonador("Openllet (Pellet)", OpenlletReasonerFactory.getInstance()),
            new EntradaRazonador("JFact (FaCT++)",   new JFactFactory())
        );

        // 3. Ejecutar benchmark para cada razonador
        List<ResultadoBenchmark> resultados = new ArrayList<>();
        for (EntradaRazonador entrada : razonadores) {
            ResultadoBenchmark r = ejecutarBenchmark(entrada, merged);
            resultados.add(r);
        }

        // 4. Imprimir tabla comparativa
        imprimirTabla(resultados);
        imprimirClasificaciones(resultados);
        imprimirResumen(resultados);
    }

    // ────────────────────────────────────────────────────────────────────────
    // Carga y fusión de ontologías
    // ────────────────────────────────────────────────────────────────────────
    private static OWLOntology cargarOntologias() throws Exception {
        System.out.println(CYAN + "Cargando ontologías..." + RESET);

        OWLOntologyManager manager = OWLManager.createOWLOntologyManager();

        // Ontología base (incluye clasificadores)
        File baseFile = new File(BASE_TTL);
        verificarArchivo(baseFile, "Ontología base");
        OWLOntology base = manager.loadOntologyFromOntologyDocument(baseFile);

        // Fusionar en una sola ontología para razonar
        OWLOntology merged = manager.createOntology(
            IRI.create("http://www.poker-ontology.org/benchmark")
        );
        manager.addAxioms(merged, base.getAxioms());

        // Cargar los 10 archivos de instancias
        System.out.println("  Cargando instancias...");
        for (String path : INST_TTLS) {
            File f = new File(path);
            verificarArchivo(f, f.getName());
            OWLOntology inst = manager.loadOntologyFromOntologyDocument(f);
            manager.addAxioms(merged, inst.getAxioms());
        }

        System.out.printf("%n  ✓ Axiomas totales en la ontología fusionada: %d%n%n",
            merged.getAxiomCount());
        return merged;
    }

    private static void verificarArchivo(File f, String nombre) {
        if (!f.exists()) {
            System.err.println(RED + "[ERROR] " + nombre + " no encontrado en: "
                + f.getAbsolutePath() + RESET);
            System.exit(1);
        }
        System.out.printf("  ✓ %-20s → %s%n", nombre, f.getAbsolutePath());
    }

    // ────────────────────────────────────────────────────────────────────────
    // Benchmark de un razonador
    // ────────────────────────────────────────────────────────────────────────
    private static ResultadoBenchmark ejecutarBenchmark(
            EntradaRazonador entrada, OWLOntology ontologia) {

        System.out.println(BOLD + "━━━ " + entrada.nombre + " ━━━" + RESET);
        ResultadoBenchmark res = new ResultadoBenchmark(entrada.nombre);

        OWLDataFactory factory = ontologia.getOWLOntologyManager().getOWLDataFactory();
        MemoryMXBean memBean   = ManagementFactory.getMemoryMXBean();

        try {
            // ── Memoria antes ────────────────────────────────────────────────
            System.gc();
            long memAntesMB = memBean.getHeapMemoryUsage().getUsed() / (1024 * 1024);

            // ── Inicialización ───────────────────────────────────────────────
            long t0 = System.currentTimeMillis();
            OWLReasoner reasoner = entrada.factory.createReasoner(
                ontologia, new SimpleConfiguration()
            );
            long tInit = System.currentTimeMillis() - t0;
            res.tiempoInicMs = tInit;

            // ── Precomputación ───────────────────────────────────────────────
            long t1 = System.currentTimeMillis();
            reasoner.precomputeInferences(
                InferenceType.CLASS_HIERARCHY,
                InferenceType.CLASS_ASSERTIONS,
                InferenceType.OBJECT_PROPERTY_ASSERTIONS
            );
            long tPrecomp = System.currentTimeMillis() - t1;
            res.tiempoPrecompMs = tPrecomp;
            res.tiempoTotalMs   = tInit + tPrecomp;

            // ── Memoria después ──────────────────────────────────────────────
            long memDespuesMB = memBean.getHeapMemoryUsage().getUsed() / (1024 * 1024);
            res.memAntesMB   = memAntesMB;
            res.memDespuesMB = memDespuesMB;
            res.memDeltaMB   = memDespuesMB - memAntesMB;

            // ── Consistencia ─────────────────────────────────────────────────
            res.consistente = reasoner.isConsistent();
            System.out.printf("  Consistencia      : %s%n",
                res.consistente ? GREEN + "✓ CONSISTENTE" + RESET : RED + "✗ INCONSISTENTE" + RESET);

            if (!res.consistente) {
                reasoner.dispose();
                return res;
            }

            // ── Jerarquía de clases ──────────────────────────────────────────
            res.numClasesJerarquia = reasoner
                .getSubClasses(factory.getOWLThing(), false)
                .getFlattened().size();

            // ── Clasificación por clase de mano ──────────────────────────────
            long totalInferencias = 0;
            for (String nombreClase : CLASES_MANO) {
                OWLClass clase = factory.getOWLClass(IRI.create(BASE_IRI + nombreClase));
                NodeSet<OWLNamedIndividual> instancias =
                    reasoner.getInstances(clase, false);
                int n = instancias.getFlattened().size();
                res.instanciasPorClase.put(nombreClase, n);
                totalInferencias += n;
            }
            res.totalInferencias = totalInferencias;

            // ── Inferencias detalladas por instancia ─────────────────────────
            OWLClass manoClass = factory.getOWLClass(IRI.create(BASE_IRI + "Mano"));
            NodeSet<OWLNamedIndividual> todasManos =
                reasoner.getInstances(manoClass, false);

            for (OWLNamedIndividual ind : todasManos.getFlattened()) {
                NodeSet<OWLClass> tipos = reasoner.getTypes(ind, true);
                List<String> tiposNombre = new ArrayList<>();
                for (OWLClass c : tipos.getFlattened()) {
                    if (!c.isOWLThing()) {
                        tiposNombre.add(c.getIRI().getShortForm());
                    }
                }
                res.clasificacionIndividual.put(
                    ind.getIRI().getShortForm(), tiposNombre
                );
            }

            System.out.printf("  Init              : %d ms%n",  tInit);
            System.out.printf("  Precomputación    : %d ms%n",  tPrecomp);
            System.out.printf("  Total             : %d ms%n",  res.tiempoTotalMs);
            System.out.printf("  Memoria delta     : %+d MB%n", res.memDeltaMB);
            System.out.printf("  Clases inferidas  : %d%n",     res.numClasesJerarquia);
            System.out.printf("  Inferencias totales: %d%n%n",  res.totalInferencias);

            reasoner.dispose();

        } catch (Exception e) {
            res.error = e.getMessage();
            System.out.println(RED + "  [ERROR] " + e.getMessage() + RESET + "\n");
        }

        return res;
    }

    // ────────────────────────────────────────────────────────────────────────
    // Impresión de resultados
    // ────────────────────────────────────────────────────────────────────────
    private static void imprimirTabla(List<ResultadoBenchmark> resultados) {
        System.out.println(BOLD + CYAN);
        System.out.println("╔══════════════════════════════════════════════════════════════════════╗");
        System.out.println("║              TABLA COMPARATIVA DE RAZONADORES                       ║");
        System.out.println("╚══════════════════════════════════════════════════════════════════════╝");
        System.out.println(RESET);

        String fmt = "%-22s │ %10s │ %12s │ %10s │ %10s │ %8s │ %12s%n";
        System.out.printf(BOLD + fmt + RESET,
            "Razonador", "Init (ms)", "Precomp (ms)", "Total (ms)",
            "ΔMem (MB)", "Consist.", "Inferencias");
        System.out.println("─".repeat(95));

        for (ResultadoBenchmark r : resultados) {
            if (r.error != null) {
                System.out.printf("%-22s │ %s%n", r.nombre, RED + "ERROR: " + r.error + RESET);
                continue;
            }
            System.out.printf(fmt,
                r.nombre,
                r.tiempoInicMs,
                r.tiempoPrecompMs,
                r.tiempoTotalMs,
                (r.memDeltaMB >= 0 ? "+" : "") + r.memDeltaMB,
                r.consistente ? "SI" : "NO",
                r.totalInferencias
            );
        }
        System.out.println();
    }

    private static void imprimirClasificaciones(List<ResultadoBenchmark> resultados) {
        System.out.println(BOLD + CYAN);
        System.out.println("╔══════════════════════════════════════════════════════════════════════╗");
        System.out.println("║           INSTANCIAS CLASIFICADAS POR CLASE DE MANO                 ║");
        System.out.println("╚══════════════════════════════════════════════════════════════════════╝");
        System.out.println(RESET);

        // Cabecera dinámica
        StringBuilder cabecera = new StringBuilder(String.format("%-14s", "Clase"));
        for (ResultadoBenchmark r : resultados) {
            cabecera.append(String.format(" │ %-16s", r.nombre));
        }
        System.out.println(BOLD + cabecera + RESET);
        System.out.println("─".repeat(14 + resultados.size() * 20));

        for (String clase : CLASES_MANO) {
            StringBuilder fila = new StringBuilder(String.format("%-14s", clase));
            for (ResultadoBenchmark r : resultados) {
                int n = r.instanciasPorClase.getOrDefault(clase, -1);
                fila.append(String.format(" │ %-16s",
                    n == -1 ? RED + "ERROR" + RESET : String.valueOf(n)));
            }
            System.out.println(fila);
        }
        System.out.println();
    }

    private static void imprimirResumen(List<ResultadoBenchmark> resultados) {
        System.out.println(BOLD + CYAN);
        System.out.println("╔══════════════════════════════════════════════════════════════════════╗");
        System.out.println("║                     CLASIFICACIÓN INDIVIDUAL                        ║");
        System.out.println("╚══════════════════════════════════════════════════════════════════════╝");
        System.out.println(RESET);

        // Usar el primer razonador exitoso como referencia
        ResultadoBenchmark ref = resultados.stream()
            .filter(r -> r.error == null && !r.clasificacionIndividual.isEmpty())
            .findFirst().orElse(null);

        if (ref == null) {
            System.out.println(RED + "  No hay clasificaciones disponibles." + RESET);
            return;
        }

        // Ordenar instancias alfabéticamente
        List<String> instancias = new ArrayList<>(ref.clasificacionIndividual.keySet());
        Collections.sort(instancias);

        for (String ind : instancias) {
            System.out.printf(BOLD + "  %-20s" + RESET, ind);
            for (ResultadoBenchmark r : resultados) {
                List<String> tipos = r.clasificacionIndividual.getOrDefault(ind, List.of("?"));
                System.out.printf("  [%s: %s]", r.nombre, String.join(", ", tipos));
            }
            System.out.println();
        }
        System.out.println();

        // Ganador en velocidad
        ResultadoBenchmark masFast = resultados.stream()
            .filter(r -> r.error == null)
            .min(Comparator.comparingLong(r -> r.tiempoTotalMs))
            .orElse(null);
        if (masFast != null) {
            System.out.println(GREEN + BOLD
                + "  ⚡ Razonador más rápido: " + masFast.nombre
                + " (" + masFast.tiempoTotalMs + " ms)" + RESET);
        }

        ResultadoBenchmark menosMem = resultados.stream()
            .filter(r -> r.error == null)
            .min(Comparator.comparingLong(r -> r.memDeltaMB))
            .orElse(null);
        if (menosMem != null) {
            System.out.println(GREEN + BOLD
                + "  💾 Menor consumo de memoria: " + menosMem.nombre
                + " (+" + menosMem.memDeltaMB + " MB)" + RESET);
        }
        System.out.println();
    }

    private static void banner() {
        System.out.println(BOLD + CYAN);
        System.out.println("╔══════════════════════════════════════════════════════════════════════╗");
        System.out.println("║         BENCHMARK DE RAZONADORES OWL — ONTOLOGÍA DE PÓKER           ║");
        System.out.println("║              HermiT  ·  Openllet (Pellet)  ·  JFact (FaCT++)        ║");
        System.out.println("╚══════════════════════════════════════════════════════════════════════╝");
        System.out.println(RESET);
    }

    // ────────────────────────────────────────────────────────────────────────
    // Clases auxiliares
    // ────────────────────────────────────────────────────────────────────────
    static class EntradaRazonador {
        String nombre;
        OWLReasonerFactory factory;
        EntradaRazonador(String nombre, OWLReasonerFactory factory) {
            this.nombre  = nombre;
            this.factory = factory;
        }
    }

    static class ResultadoBenchmark {
        String nombre;
        long   tiempoInicMs    = 0;
        long   tiempoPrecompMs = 0;
        long   tiempoTotalMs   = 0;
        long   memAntesMB      = 0;
        long   memDespuesMB    = 0;
        long   memDeltaMB      = 0;
        boolean consistente    = false;
        long   numClasesJerarquia = 0;
        long   totalInferencias   = 0;
        String error = null;
        Map<String, Integer>      instanciasPorClase    = new LinkedHashMap<>();
        Map<String, List<String>> clasificacionIndividual = new LinkedHashMap<>();

        ResultadoBenchmark(String nombre) { this.nombre = nombre; }
    }
}
