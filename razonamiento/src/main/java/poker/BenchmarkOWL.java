package poker;

import org.semanticweb.owlapi.apibinding.OWLManager;
import org.semanticweb.owlapi.model.*;
import org.semanticweb.owlapi.reasoner.*;
import org.semanticweb.owlapi.util.SimpleIRIMapper;

// Razonadores OWL
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
 * BenchmarkOWL compara los razonadores OWL HermiT, Openllet (Pellet) y JFact (FaCT++)
 * sobre ontologías bajo el dominio del juego Póker Texas Hold'em.
 *
 * Uso:
 *   java -jar poker-reasoner.jar <ontologia.ttl> <instancias.ttl>
 * 
 * Se puede designar a la ejecución del experimento una cantidad inicial y máxima de memoria RAM, como por ejemplo:
 * 
 *   java -Xms2g -Xmx4g -jar poker-reasoner.jar <ontologia.ttl> <instancias.ttl>
 *
 * El IRI base se extrae automáticamente de la ontología cargada,
 * por lo que el benchmark funciona con cualquier variante de póker con barajas customizadas.
 *
 * Métricas por razonador:
 *   • carga_ms: Tiempo (milisegundos) de lectura de TTL desde disco y construcción del OWLOntology fusionado.
 *   • init_ms: Tiempo (milisegundos) de creación del razonador.
 *   • precomp_ms: Tiempo (milisegundos) de chequeo de consistencia y precomputación de jerarquía de clases.
 *   • total_ms: Tiempo (milisegundos) de la suma de los tres anteriores (costo real de razonar desde cero).
 *   • mem_antes_mb: Heap usada antes de la precomputación (MB).
 *   • mem_despues_mb: Heap usada después de la precomputación (MB).
 *   • mem_delta_mb: Diferencia de heap antes/después de la precomputación (MB).
 *   • consistente: si la ontología es consistente según el razonador.
 *   • clases_jerarquia: número de clases en la jerarquía inferida.
 *   • inst_<Clase>: número de individuos clasificados bajo cada clase de mano.
 *   • total_inferencias: suma de inst_<Clase> sobre todas las clases de mano.
 */
public class BenchmarkOWL {

    /** Ruta al archivo TTL de la ontología base (TBox + ABox de baraja). */
    private static String BASE_TTL;

    /** Ruta al archivo TTL con las instancias de manos (ABox). */
    private static String INST_TTL;

    /** IRI base de la ontología, extraído automáticamente al cargarla. */
    private static String BASE_IRI;

    /** IRI de la ontología local, usado para resolver owl:imports sin salir a red. */
    private static String BASE_ONTOLOGY_IRI;

    /** Carpeta de destino para los archivos .csv de resultados. */
    private static final String RESULTADOS_DIR = "../resultados";

    /** Timestamp compartido por todos los archivos generados en esta ejecución. */
    private static final String TIMESTAMP =
        LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss"));

    /** Nombres de las clases de mano consultadas al razonador, en orden de menor a mayor valor. */
    private static final String[] CLASES_MANO = {
        "CartaAlta", "Par", "DoblePar", "Trio", "Escalera", "Color", "Full", "Poker", "EscaleraColor", "EscaleraReal"
    };

    private static final String RESET = "\u001B[0m";
    private static final String BOLD = "\u001B[1m";
    private static final String CYAN = "\u001B[36m";
    private static final String GREEN = "\u001B[32m";
    private static final String RED = "\u001B[31m";
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

        detectarBaseIRI();

        banner();

        List<EntradaRazonador> razonadores = Arrays.asList(
            new EntradaRazonador("HermiT", new ReasonerFactory()),
            new EntradaRazonador("Openllet (Pellet)", OpenlletReasonerFactory.getInstance()),
            new EntradaRazonador("JFact (FaCT++)", new JFactFactory())
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

    /**
     * Extrae el IRI base desde la ontología base y lo asigna a {@code BASE_IRI}.
     * Se llama una única vez desde {@code main()} antes de iniciar el benchmark.
     * No carga las instancias ni construye la ontología fusionada, por lo que
     * no deja objetos pesados en el heap antes de que comience la medición.
     *
     * @throws Exception si el archivo no existe o la ontología no declara IRI.
     */
    private static void detectarBaseIRI() throws Exception {
        OWLOntologyManager manager = OWLManager.createOWLOntologyManager();
        File baseFile = new File(BASE_TTL);
        verificarArchivo(baseFile, "Ontología base");
        OWLOntology base = manager.loadOntologyFromOntologyDocument(baseFile);
        String ontIRI = base.getOntologyID()
            .getOntologyIRI()
            .map(IRI::toString)
            .orElseThrow(() -> new IllegalStateException(
                "La ontología base no declara un IRI (falta <iri> a owl:Ontology)."));
        BASE_ONTOLOGY_IRI = ontIRI;
        BASE_IRI = ontIRI + "#";
        System.out.printf("  IRI base detectado : %s%n", BASE_IRI);
        manager.removeOntology(base);
    }

    /**
     * Carga la ontología base y el archivo de instancias
     * y los fusiona en una única ontología anónima lista para razonar.
     *
     * Cada invocación crea un {@code OWLOntologyManager} limpio y libera
     * explícitamente las ontologías intermedias (base e instancias) una vez
     * copiados sus axiomas a {@code merged}, minimizando la presión sobre el
     * heap durante la medición de cada razonador.
     *
     * @return ontología fusionada (TBox + ABox).
     * @throws Exception si algún archivo no existe.
     */
    private static OWLOntology cargarOntologias() throws Exception {
        OWLOntologyManager manager = OWLManager.createOWLOntologyManager();

        File baseFile = new File(BASE_TTL);
        verificarArchivo(baseFile, "Ontología base");
        manager.getIRIMappers().add(new SimpleIRIMapper(
            IRI.create(BASE_ONTOLOGY_IRI),
            IRI.create(baseFile.toURI())
        ));
        OWLOntology base = manager.loadOntologyFromOntologyDocument(baseFile);
        OWLOntology merged = manager.createOntology();
        manager.addAxioms(merged, base.getAxioms());

        File instFile = new File(INST_TTL);
        verificarArchivo(instFile, instFile.getName());
        OWLOntology inst = manager.loadOntologyFromOntologyDocument(instFile);
        manager.addAxioms(merged, inst.getAxioms());
        manager.removeOntology(inst);
        manager.removeOntology(base);

        System.out.printf("  Axiomas totales en la ontología fusionada: %d%n",
            merged.getAxiomCount());
        return merged;
    }

    /**
     * Verifica que el archivo {@code f} exista y lo imprime en consola.
     * Termina el proceso si no se encuentra.
     *
     * @param f archivo a verificar.
     * @param nombre etiqueta descriptiva para el mensaje de error.
     */
    private static void verificarArchivo(File f, String nombre) {
        if (!f.exists()) {
            System.err.println(RED + "[ERROR] " + nombre + " no encontrado en: "
                + f.getAbsolutePath() + RESET);
            System.exit(1);
        }
        System.out.printf("  %-20s : %s%n", nombre, f.getAbsolutePath());
    }

    /**
     * Ejecuta el benchmark completo para un único razonador.
     *
     * Cada invocación recarga la ontología desde disco con un manager limpio,
     * garantizando que ningún razonador herede estado de caché del anterior.
     * Las fases medidas son: carga TTL, inicialización del razonador y
     * precomputación de inferencias. Si el razonador falla o la ontología es
     * inconsistente, el error queda registrado en {@link ResultadoBenchmark#error}
     * y el método retorna igualmente sin lanzar excepción.
     *
     * @param entrada par (nombre, factory) que identifica al razonador.
     * @return resultado con todas las métricas medidas, o con {@code error} no nulo si falló.
     */
    private static ResultadoBenchmark ejecutarBenchmark(EntradaRazonador entrada) {

        System.out.println(BOLD + "\n[ " + entrada.nombre + " ]" + RESET);
        ResultadoBenchmark res = new ResultadoBenchmark(entrada.nombre);

        MemoryMXBean memBean = ManagementFactory.getMemoryMXBean();

        try {
            System.gc();
            long memAntesMB = memBean.getHeapMemoryUsage().getUsed() / (1024 * 1024);

            long tCarga0 = System.currentTimeMillis();
            System.out.println("  Cargando ontologias...");
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
            res.consistente = reasoner.isConsistent();
            System.out.printf("  Consistencia      : %s%n",
                res.consistente ? GREEN + "CONSISTENTE" + RESET : RED + "INCONSISTENTE" + RESET);

            if (res.consistente) {
                reasoner.precomputeInferences(InferenceType.CLASS_HIERARCHY);
            }

            long tPrecomp = System.currentTimeMillis() - t1;
            res.tiempoPrecompMs = tPrecomp;
            res.tiempoTotalMs = tCarga + tInit + tPrecomp;

            long memDespuesMB = memBean.getHeapMemoryUsage().getUsed() / (1024 * 1024);
            res.memAntesMB = memAntesMB;
            res.memDespuesMB = memDespuesMB;
            res.memDeltaMB = memDespuesMB - memAntesMB;

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

            System.out.println("  Inferencias en tiempo real:");
            for (OWLNamedIndividual ind : todasManos.getFlattened()) {
                NodeSet<OWLClass> tipos = reasoner.getTypes(ind, true);
                List<String> tiposNombre = new ArrayList<>();
                for (OWLClass c : tipos.getFlattened()) {
                    if (!c.isOWLThing()) {
                        tiposNombre.add(c.getIRI().getShortForm());
                    }
                }
                System.out.printf("  " + YELLOW + "%-45s" + RESET + " : %s%n",
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

            System.out.printf("  %-22s : %d ms%n",  "Carga",               tCarga);
            System.out.printf("  %-22s : %d ms%n",  "Init",                tInit);
            System.out.printf("  %-22s : %d ms%n",  "Precomputacion",      tPrecomp);
            System.out.printf("  %-22s : %d ms%n",  "Total",               res.tiempoTotalMs);
            System.out.printf("  %-22s : %+d MB%n", "Memoria delta",       res.memDeltaMB);
            System.out.printf("  %-22s : %d%n",     "Clases inferidas",    res.numClasesJerarquia);
            System.out.printf("  %-22s : %d%n%n",   "Inferencias totales", res.totalInferencias);

            reasoner.dispose();

        } catch (Exception e) {
            res.error = e.getMessage();
            System.out.println(RED + "  [ERROR] " + e.getMessage() + RESET + "\n");
        }

        return res;
    }

    /**
     * Imprime la tabla comparativa de métricas de rendimiento por razonador.
     *
     * @param resultados lista de resultados, uno por razonador.
     */
    private static void imprimirTabla(List<ResultadoBenchmark> resultados) {
        System.out.println(BOLD + CYAN);
        System.out.println("╔══════════════════════════════════════════════════════════════════════╗");
        System.out.println("║                   TABLA COMPARATIVA DE RAZONADORES                   ║");
        System.out.println("╚══════════════════════════════════════════════════════════════════════╝");
        System.out.println(RESET);

        String fmt = "%-22s │ %10s │ %10s │ %12s │ %10s │ %10s │ %8s │ %12s%n";
        System.out.printf(BOLD + fmt + RESET,
            "Razonador", "Carga (ms)", "Init (ms)", "Precomp (ms)", "Total (ms)",
            "Mem (MB)", "Consist.", "Inferencias");
        System.out.println("─".repeat(110));

        for (ResultadoBenchmark r : resultados) {
            if (r.error != null) {
                System.out.printf("%-22s │ %s%n", r.nombre, RED + "TIMEOUT/ERROR: " + r.error + RESET);
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

    /**
     * Imprime cuántos individuos clasificó cada razonador bajo cada clase de mano.
     *
     * @param resultados lista de resultados, uno por razonador.
     */
    private static void imprimirClasificaciones(List<ResultadoBenchmark> resultados) {
        System.out.println(BOLD + CYAN);
        System.out.println("╔══════════════════════════════════════════════════════════════════════╗");
        System.out.println("║               INSTANCIAS CLASIFICADAS POR CLASE DE MANO              ║");
        System.out.println("╚══════════════════════════════════════════════════════════════════════╝");
        System.out.println(RESET);

        int colClase = 15;
        int colRazon = 20;

        StringBuilder cabecera = new StringBuilder(
            BOLD + String.format("%-" + colClase + "s", "Clase") + RESET);
        for (ResultadoBenchmark r : resultados) {
            cabecera.append(String.format(" │ %-" + colRazon + "s", r.nombre));
        }
        System.out.println(cabecera);
        System.out.println("─".repeat(colClase + resultados.size() * (colRazon + 3)));

        for (String clase : CLASES_MANO) {
            StringBuilder fila = new StringBuilder(String.format("%-" + colClase + "s", clase));
            for (ResultadoBenchmark r : resultados) {
                if (r.error != null) {
                    fila.append(" │ ").append(RED)
                        .append(String.format("%-" + colRazon + "s", "TIMEOUT"))
                        .append(RESET);
                } else {
                    int n = r.instanciasPorClase.getOrDefault(clase, 0);
                    fila.append(String.format(" │ %-" + colRazon + "s", n > 0
                        ? GREEN + n + RESET
                        : String.valueOf(n)));
                }
            }
            System.out.println(fila);
        }
        System.out.println();
    }

    /**
     * Imprime la clasificación individual de cada mano según cada razonador.
     *
     * @param resultados lista de resultados, uno por razonador.
     */
    private static void imprimirResumen(List<ResultadoBenchmark> resultados) {
        System.out.println(BOLD + CYAN);
        System.out.println("╔══════════════════════════════════════════════════════════════════════╗");
        System.out.println("║                        CLASIFICACION INDIVIDUAL                      ║");
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
                if (r.error != null) {
                    System.out.printf("  [%s: %s]", r.nombre,
                        RED + "TIMEOUT" + RESET);
                } else {
                    List<String> tipos = r.clasificacionIndividual.getOrDefault(ind, List.of("-"));
                    String clases = tipos.isEmpty() ? RED + "(sin clase)" + RESET
                                                    : GREEN + String.join(", ", tipos) + RESET;
                    System.out.printf("  [%s: %s]", r.nombre, clases);
                }
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
                + "  Razonador mas rapido    : " + masFast.nombre
                + " (" + masFast.tiempoTotalMs + " ms)" + RESET);
        }

        ResultadoBenchmark menosMem = resultados.stream()
            .filter(r -> r.error == null)
            .min(Comparator.comparingLong(r -> r.memDeltaMB))
            .orElse(null);
        if (menosMem != null) {
            System.out.println(GREEN + BOLD
                + "  Menor consumo de memoria: " + menosMem.nombre
                + " (+" + menosMem.memDeltaMB + " MB)" + RESET);
        }
        System.out.println();
    }

    /**
     * Genera un único archivo CSV con dos secciones:
     * resumen de métricas por razonador y clasificación individual.
     * El nombre incluye el nombre de la ontología y el timestamp.
     * Los razonadores con TIMEOUT aparecen en la sección de métricas
     * con TIMEOUT en todas sus celdas, y se omiten en clasificación individual.
     *
     * @param resultados lista de resultados, uno por razonador.
     */
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

        String nombre = variante + "_benchmark_" + TIMESTAMP + ".csv";
        Path archivo = dirPath.resolve(nombre);

        try (PrintWriter pw = new PrintWriter(
                new OutputStreamWriter(
                    new FileOutputStream(archivo.toFile()), StandardCharsets.UTF_8))) {

            pw.println("# RESUMEN DE METRICAS POR RAZONADOR");

            StringBuilder cabecera1 = new StringBuilder(
                "variante,razonador,carga_ms,init_ms,precomp_ms,total_ms," +
                "mem_antes_mb,mem_despues_mb,mem_delta_mb," +
                "consistente,clases_jerarquia,total_inferencias");
            for (String c : CLASES_MANO) cabecera1.append(",inst_").append(c);
            pw.println(cabecera1);

            for (ResultadoBenchmark r : resultados) {
                if (r.error != null) {
                    String t = csvEscape(r.error);
                    StringBuilder fila = new StringBuilder();
                    fila.append(csvEscape(variante)).append(',');
                    fila.append(csvEscape(r.nombre)).append(',');
                    for (int i = 0; i < 10; i++) fila.append(t).append(',');
                    fila.append(t);
                    for (int i = 0; i < CLASES_MANO.length; i++) fila.append(',').append(t);
                    pw.println(fila);
                    continue;
                }
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

            pw.println();

            pw.println("# CLASIFICACION INDIVIDUAL");
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
            System.err.println(RED + "[CSV] Error escribiendo resultados: " + e.getMessage() + RESET);
        }
    }

    /**
     * Aplica pequeñas modificaciones a un valor CSV: lo envuelve entre comillas dobles
     * si contiene comas, comillas o saltos de línea, duplicando las comillas internas.
     *
     * @param v valor a escapar; {@code null} se trata como cadena vacía.
     * @return valor seguro para insertar directamente en un campo CSV.
     */
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
        System.out.println("║           BENCHMARK DE RAZONADORES OWL - ONTOLOGIA DE POKER          ║");
        System.out.println("║            HermiT  ·  Openllet (Pellet)  ·  JFact (FaCT++)           ║");
        System.out.println("╚══════════════════════════════════════════════════════════════════════╝");
        System.out.println(RESET);
    }

    /** Par (nombre, factory) que identifica a un razonador OWL en el benchmark. */
    static class EntradaRazonador {
        String nombre;
        OWLReasonerFactory factory;
        EntradaRazonador(String nombre, OWLReasonerFactory factory) {
            this.nombre = nombre;
            this.factory = factory;
        }
    }

    /** Acumula todas las métricas de una ejecución de benchmark para un único razonador. */
    static class ResultadoBenchmark {
        String nombre;
        long tiempoCargaMs = 0;
        long tiempoInicMs = 0;
        long tiempoPrecompMs = 0;
        long tiempoTotalMs = 0;
        long memAntesMB = 0;
        long memDespuesMB = 0;
        long memDeltaMB = 0;
        boolean consistente = false;
        long numClasesJerarquia = 0;
        long totalInferencias = 0;
        String error = null;
        Map<String, Integer>      instanciasPorClase    = new LinkedHashMap<>();
        Map<String, List<String>> clasificacionIndividual = new LinkedHashMap<>();

        ResultadoBenchmark(String nombre) { this.nombre = nombre; }
    }
}