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

import java.io.*;
import java.lang.management.ManagementFactory;
import java.lang.management.MemoryMXBean;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;

/**
 * BenchmarkOWL — compara HermiT, Openllet (Pellet) y JFact (FaCT++)
 * sobre una ontología de póker.
 *
 * Uso:
 *   java -jar poker-reasoner.jar <ontologia.ttl> <instancias.ttl>
 *
 * El IRI base se extrae automáticamente de la ontología cargada,
 * por lo que el benchmark funciona con cualquier variante de baraja.
 *
 * Métricas por razonador (todas las temporales en milisegundos):
 *   • carga_ms    — lectura de TTL desde disco y construcción del OWLOntology fusionado
 *   • init_ms     — creación del razonador (createReasoner)
 *   • precomp_ms  — precomputación de jerarquía, aserciones de clase y propiedades de objeto
 *   • total_ms    — suma de los tres anteriores (costo real de razonar desde cero)
 *   • mem_delta_mb — diferencia de heap usada antes/después de la precomputación (MB)
 *   • consistente  — si la ontología es consistente según el razonador
 *   • clases_jerarquia — número de clases en la jerarquía inferida
 *   • inst_<Clase> — número de individuos clasificados bajo cada clase de mano
 *   • total_inferencias — suma de inst_<Clase> sobre todas las clases de mano
 */
public class BenchmarkOWL {

    private static String BASE_TTL;
    private static String INST_TTL;

    private static String BASE_IRI;

    private static final String RESULTADOS_DIR = "../../resultados";

    private static final String TIMESTAMP =
        LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss"));

    private static final String[] CLASES_MANO = {
        "CartaAlta", "Par", "DoblePar", "Trio",
        "Escalera", "Color", "Full", "Poker", "EscaleraColor", "EscaleraReal"
    };

    private static final String RESET  = "\u001B[0m";
    private static final String BOLD   = "\u001B[1m";
    private static final String CYAN   = "\u001B[36m";
    private static final String GREEN  = "\u001B[32m";
    private static final String RED    = "\u001B[31m";
    private static final String YELLOW = "\u001B[33m";

    public static void main(String[] args) throws Exception {

        if (args.length != 2) {
            System.err.println(RED
                + "Uso: java -jar poker-reasoner.jar <ontologia.ttl> <instancias.ttl>"
                + RESET);
            System.exit(1);
        }
        BASE_TTL = args[0];
        INST_TTL = args[1];

        cargarOntologias();

        banner();

        List<EntradaRazonador> razonadores = Arrays.asList(
            new EntradaRazonador("HermiT",           new ReasonerFactory()),
            new EntradaRazonador("Openllet (Pellet)", OpenlletReasonerFactory.getInstance()),
            new EntradaRazonador("JFact (FaCT++)",    new JFactFactory())
        );

        List<ResultadoBenchmark> resultados = new ArrayList<>();
        for (EntradaRazonador entrada : razonadores) {
            ResultadoBenchmark r = ejecutarBenchmark(entrada);
            resultados.add(r);
        }

        imprimirTabla(resultados);
        imprimirClasificaciones(resultados);
        imprimirResumen(resultados);

        guardarCSV(resultados);
    }

    private static OWLOntology cargarOntologias() throws Exception {
        OWLOntologyManager manager = OWLManager.createOWLOntologyManager();

        File baseFile = new File(BASE_TTL);
        verificarArchivo(baseFile, "Ontología base");
        OWLOntology base = manager.loadOntologyFromOntologyDocument(baseFile);

        if (BASE_IRI == null) {
            String ontIRI = base.getOntologyID()
                .getOntologyIRI()
                .map(IRI::toString)
                .orElseThrow(() -> new IllegalStateException(
                    "La ontología base no declara un IRI (falta <iri> a owl:Ontology)."));
            BASE_IRI = ontIRI + "#";
            System.out.printf("  IRI base detectado : %s%n", BASE_IRI);
        }

        OWLOntology merged = manager.createOntology();
        manager.addAxioms(merged, base.getAxioms());

        File instFile = new File(INST_TTL);
        verificarArchivo(instFile, instFile.getName());
        OWLOntology inst = manager.loadOntologyFromOntologyDocument(instFile);
        manager.addAxioms(merged, inst.getAxioms());

        System.out.printf("  Axiomas totales en la ontología fusionada: %d%n",
            merged.getAxiomCount());
        return merged;
    }

    private static void verificarArchivo(File f, String nombre) {
        if (!f.exists()) {
            System.err.println(RED + "[ERROR] " + nombre + " no encontrado en: "
                + f.getAbsolutePath() + RESET);
            System.exit(1);
        }
        System.out.printf("  %-20s → %s%n", nombre, f.getAbsolutePath());
    }

    private static ResultadoBenchmark ejecutarBenchmark(EntradaRazonador entrada) {

        System.out.println(BOLD + "━━━ " + entrada.nombre + " ━━━" + RESET);
        ResultadoBenchmark res = new ResultadoBenchmark(entrada.nombre);

        MemoryMXBean memBean = ManagementFactory.getMemoryMXBean();

        try {
            System.gc();
            long memAntesMB = memBean.getHeapMemoryUsage().getUsed() / (1024 * 1024);

            long tCarga0 = System.currentTimeMillis();
            System.out.println(CYAN + "  Cargando ontologías..." + RESET);
            OWLOntology ontologia = cargarOntologias();
            long tCarga = System.currentTimeMillis() - tCarga0;
            res.tiempoCargaMs = tCarga;

            OWLDataFactory factory = ontologia.getOWLOntologyManager().getOWLDataFactory();

            long t0 = System.currentTimeMillis();
            OWLReasoner reasoner = entrada.factory.createReasoner(
                ontologia, new SimpleConfiguration()
            );
            long tInit = System.currentTimeMillis() - t0;
            res.tiempoInicMs = tInit;

            long t1 = System.currentTimeMillis();
            reasoner.precomputeInferences(
                InferenceType.CLASS_HIERARCHY,
                InferenceType.CLASS_ASSERTIONS,
                InferenceType.OBJECT_PROPERTY_ASSERTIONS
            );
            long tPrecomp = System.currentTimeMillis() - t1;
            res.tiempoPrecompMs = tPrecomp;
            res.tiempoTotalMs   = tCarga + tInit + tPrecomp;

            long memDespuesMB = memBean.getHeapMemoryUsage().getUsed() / (1024 * 1024);
            res.memAntesMB   = memAntesMB;
            res.memDespuesMB = memDespuesMB;
            res.memDeltaMB   = memDespuesMB - memAntesMB;

            res.consistente = reasoner.isConsistent();
            System.out.printf("  Consistencia      : %s%n",
                res.consistente ? GREEN + "CONSISTENTE" + RESET : RED + "✗ INCONSISTENTE" + RESET);

            if (!res.consistente) {
                reasoner.dispose();
                return res;
            }

            res.numClasesJerarquia = reasoner
                .getSubClasses(factory.getOWLThing(), false)
                .getFlattened().size();

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

            OWLClass manoClass = factory.getOWLClass(IRI.create(BASE_IRI + "Mano"));
            NodeSet<OWLNamedIndividual> todasManos =
                reasoner.getInstances(manoClass, false);

            System.out.println(CYAN + "  [Inferencias en tiempo real]" + RESET);
            for (OWLNamedIndividual ind : todasManos.getFlattened()) {
                NodeSet<OWLClass> tipos = reasoner.getTypes(ind, true);
                List<String> tiposNombre = new ArrayList<>();
                for (OWLClass c : tipos.getFlattened()) {
                    if (!c.isOWLThing()) {
                        tiposNombre.add(c.getIRI().getShortForm());
                    }
                }
                System.out.printf("  " + YELLOW + "%-45s" + RESET + " → %s%n",
                    ind.getIRI().getShortForm(),
                    tiposNombre.isEmpty()
                        ? RED + "(sin clase inferida)" + RESET
                        : GREEN + String.join(", ", tiposNombre) + RESET
                );
                res.clasificacionIndividual.put(
                    ind.getIRI().getShortForm(), tiposNombre
                );
            }
            System.out.println();

            System.out.printf("  Carga             : %d ms%n",  tCarga);
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

    private static void imprimirTabla(List<ResultadoBenchmark> resultados) {
        System.out.println(BOLD + CYAN);
        System.out.println("╔══════════════════════════════════════════════════════════════════════╗");
        System.out.println("║              TABLA COMPARATIVA DE RAZONADORES                        ║");
        System.out.println("╚══════════════════════════════════════════════════════════════════════╝");
        System.out.println(RESET);

        String fmt = "%-22s │ %10s │ %10s │ %12s │ %10s │ %10s │ %8s │ %12s%n";
        System.out.printf(BOLD + fmt + RESET,
            "Razonador", "Carga (ms)", "Init (ms)", "Precomp (ms)", "Total (ms)",
            "ΔMem (MB)", "Consist.", "Inferencias");
        System.out.println("─".repeat(110));

        for (ResultadoBenchmark r : resultados) {
            if (r.error != null) {
                System.out.printf("%-22s │ %s%n", r.nombre, RED + "ERROR: " + r.error + RESET);
                continue;
            }
            System.out.printf(fmt,
                r.nombre,
                r.tiempoCargaMs,
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
        System.out.println("║           INSTANCIAS CLASIFICADAS POR CLASE DE MANO                  ║");
        System.out.println("╚══════════════════════════════════════════════════════════════════════╝");
        System.out.println(RESET);

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
        System.out.println("║                     CLASIFICACIÓN INDIVIDUAL                         ║");
        System.out.println("╚══════════════════════════════════════════════════════════════════════╝");
        System.out.println(RESET);

        ResultadoBenchmark ref = resultados.stream()
            .filter(r -> r.error == null && !r.clasificacionIndividual.isEmpty())
            .findFirst().orElse(null);

        if (ref == null) {
            System.out.println(RED + "  No hay clasificaciones disponibles." + RESET);
            return;
        }

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

    private static void guardarCSV(List<ResultadoBenchmark> resultados) {

        String variante = Paths.get(BASE_TTL).getFileName().toString()
            .replaceAll("\\.ttl$", "");

        Path dirPath = Paths.get(RESULTADOS_DIR);
        try {
            Files.createDirectories(dirPath);
        } catch (IOException e) {
            System.err.println(RED + "[CSV] No se pudo crear " + dirPath.toAbsolutePath()
                + ": " + e.getMessage() + RESET);
            return;
        }

        guardarResumenCSV(resultados, variante, dirPath);
        guardarClasificacionCSV(resultados, variante, dirPath);
    }

    private static void guardarResumenCSV(
            List<ResultadoBenchmark> resultados, String variante, Path dir) {

        String nombre = "resumen_" + TIMESTAMP + ".csv";
        Path archivo  = dir.resolve(nombre);

        StringBuilder cabecera = new StringBuilder(
            "variante,razonador,carga_ms,init_ms,precomp_ms,total_ms," +
            "mem_antes_mb,mem_despues_mb,mem_delta_mb," +
            "consistente,clases_jerarquia,total_inferencias");
        for (String c : CLASES_MANO) cabecera.append(",inst_").append(c);

        try (PrintWriter pw = new PrintWriter(
                new OutputStreamWriter(
                    new FileOutputStream(archivo.toFile()), StandardCharsets.UTF_8))) {

            pw.println(cabecera);

            for (ResultadoBenchmark r : resultados) {
                if (r.error != null) continue;          
                StringBuilder fila = new StringBuilder();
                fila.append(csvEscape(variante)).append(',');
                fila.append(csvEscape(r.nombre)).append(',');
                fila.append(r.tiempoCargaMs).append(',');
                fila.append(r.tiempoInicMs).append(',');
                fila.append(r.tiempoPrecompMs).append(',');
                fila.append(r.tiempoTotalMs).append(',');
                fila.append(r.memAntesMB).append(',');
                fila.append(r.memDespuesMB).append(',');
                fila.append(r.memDeltaMB).append(',');
                fila.append(r.consistente ? "true" : "false").append(',');
                fila.append(r.numClasesJerarquia).append(',');
                fila.append(r.totalInferencias);
                for (String c : CLASES_MANO)
                    fila.append(',').append(r.instanciasPorClase.getOrDefault(c, 0));
                pw.println(fila);
            }

            System.out.println(GREEN + "  [CSV] " + archivo.toAbsolutePath() + RESET);

        } catch (IOException e) {
            System.err.println(RED + "[CSV] Error escribiendo resumen: " + e.getMessage() + RESET);
        }
    }

    private static void guardarClasificacionCSV(
            List<ResultadoBenchmark> resultados, String variante, Path dir) {

        String nombre = "clasificacion_" + TIMESTAMP + ".csv";
        Path archivo  = dir.resolve(nombre);

        try (PrintWriter pw = new PrintWriter(
                new OutputStreamWriter(
                    new FileOutputStream(archivo.toFile()), StandardCharsets.UTF_8))) {

            pw.println("variante,razonador,individuo,clase_inferida");

            for (ResultadoBenchmark r : resultados) {
                if (r.error != null) continue;
                for (Map.Entry<String, List<String>> e : r.clasificacionIndividual.entrySet()) {
                    String individuo = e.getKey();
                    List<String> clases = e.getValue();
                    if (clases.isEmpty()) {
                        pw.printf("%s,%s,%s,%s%n",
                            csvEscape(variante), csvEscape(r.nombre),
                            csvEscape(individuo), "");
                    } else {
                        for (String clase : clases) {
                            pw.printf("%s,%s,%s,%s%n",
                                csvEscape(variante), csvEscape(r.nombre),
                                csvEscape(individuo), csvEscape(clase));
                        }
                    }
                }
            }

            System.out.println(GREEN + "  [CSV] " + archivo.toAbsolutePath() + RESET);

        } catch (IOException e) {
            System.err.println(RED + "[CSV] Error escribiendo clasificacion: " + e.getMessage() + RESET);
        }
    }

    private static String csvEscape(String v) {
        if (v == null) return "";
        if (v.contains(",") || v.contains("\"") || v.contains("\n")) {
            return "\"" + v.replace("\"", "\"\"") + "\"";
        }
        return v;
    }

    private static void banner() {
        System.out.println(BOLD + CYAN);
        System.out.println("╔══════════════════════════════════════════════════════════════════════╗");
        System.out.println("║         BENCHMARK DE RAZONADORES OWL — ONTOLOGÍA DE PÓKER            ║");
        System.out.println("║              HermiT  ·  Openllet (Pellet)  ·  JFact (FaCT++)         ║");
        System.out.println("╚══════════════════════════════════════════════════════════════════════╝");
        System.out.println(RESET);
    }

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
        long   tiempoCargaMs  = 0;
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
