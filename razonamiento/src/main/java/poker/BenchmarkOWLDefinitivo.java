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
import java.lang.management.MemoryPoolMXBean;
import java.lang.management.MemoryType;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.concurrent.*;

/**
 * BenchmarkOWLDefinitivo compara los razonadores OWL HermiT, Openllet (Pellet) y JFact (FaCT++)
 * sobre ontologías bajo el dominio del juego Poker Texas Hold'em.
 * La ontología se carga una única vez desde disco y se comparte entre los tres razonadores.
 * Esto es debido a que HermiT es el razonador principal que funciona y se ejecuta sin límite de tiempo. Openllet y JFact
 * son secundarios: se les da a lo más 1 minuto de timeout (solo para registrar los problemas de rendimiento de estos razonadores en las tablas, 
 * que no logran clasificar en tiempo razonable, probados en TestViablidadRazonadoresOWL.java).
 *
 * Uso:
 *   java -cp target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar poker.BenchmarkOWLDefinitivo <ontologia.ttl> <instancias.ttl>
 *
 * Se puede designar a la ejecución del experimento una cantidad inicial y máxima de memoria RAM, como por ejemplo:
 *
 *   java -Xms28g -Xmx30g -cp target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar poker.BenchmarkOWLDefinitivo <ontologia.ttl> <instancias.ttl>
 *
 * El IRI base se extrae automáticamente de la ontología cargada,
 * por lo que el benchmark funciona con cualquier variante de póker con barajas customizadas.
 *
 * Métricas por razonador:
 *   • carga_ms: Tiempo (milisegundos) de lectura de TTL desde disco y construcción del OWLOntology
 *     fusionado. Se mide una única vez (la carga es compartida por los tres razonadores) y el mismo
 *     valor se replica en cada fila del CSV a modo informativo; no se suma a total_ms.
 *   • init_ms: Tiempo (milisegundos) de creación del razonador.
 *   • precomp_ms: Tiempo (milisegundos) de precomputeInferences() (jerarquía, aserciones de clase
 *     y de propiedad de objeto) más consistencia.
 *   • total_ms: Tiempo (milisegundos) de init_ms + precomp_ms (costo de razonar, sin contar la carga
 *     compartida del TTL).
 *   • mem_pico_mb: máximo de heap usado desde la creación del razonador hasta el final de
 *     precomputeInferences(), medido con {@code MemoryPoolMXBean.getPeakUsage()} (reseteado
 *     justo antes de crear el razonador, tras forzar {@code System.gc()} para partir de una
 *     base limpia).
 *   • consistente: si la ontología es consistente según el razonador.
 *   • clases_jerarquia: número de clases en la jerarquía inferida.
 *   • inst_<Clase>: número de individuos clasificados bajo cada clase de mano.
 *   • total_inferencias: suma de inst_<Clase> sobre todas las clases de mano.
 */
public class BenchmarkOWLDefinitivo {

    /** Ruta al archivo TTL de la ontología base (TBox + ABox de baraja). */
    private static String BASE_TTL;

    /** Ruta al archivo TTL con las instancias de manos (ABox). */
    private static String INST_TTL;

    /** IRI base de la ontología, extraído automáticamente al cargarla. */
    private static String BASE_IRI;

    /** IRI de la ontología local, usado para resolver owl:imports sin salir a red. */
    private static String BASE_ONTOLOGY_IRI;

    /** Tiempo (ms) de la única carga de la ontología, compartida por los tres razonadores. */
    private static long TIEMPO_CARGA_MS;

    /** Carpeta de destino para los archivos .csv de resultados. */
    private static final String RESULTADOS_DIR = "../resultados";

    /** Tiempo máximo permitido por razonador. HermiT no tiene límite; Openllet y JFact
     *  se cancelan si superan este umbral y su resultado se registra como TIMEOUT. */
    private static final long TIMEOUT_SEGUNDOS = 30;

    /** Timestamp compartido por todos los archivos generados en esta ejecución. */
    private static final String TIMESTAMP =
        LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss"));

    /** Nombres de las clases de mano consultadas al razonador, en orden de menor a mayor valor. */
    private static final String[] CLASES_MANO = {
        "CartaAlta", "Par", "DoblePar", "Trio", "Escalera", "Color", "Full", "Poker", "EscaleraColor", "EscaleraReal"
    };

    private static final String[] TIPOS_MANO_ARCHIVO = {
        "escalera_color", "escalera_real", "carta_alta", "doble_par", "escalera",
        "poker", "color", "trio", "full", "par"
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
                + "Uso: java -cp target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar poker.BenchmarkOWLDefinitivo <ontologia.ttl> <instancias.ttl>"
                + RESET);
            System.exit(1);
        }
        BASE_TTL = args[0];
        INST_TTL = args[1];

        detectarBaseIRI();

        banner();

        long tCarga0 = System.currentTimeMillis();
        System.out.println("  " + CYAN + "Cargando ontologias..." + RESET);
        OWLOntology ontologia = cargarOntologias();
        TIEMPO_CARGA_MS = System.currentTimeMillis() - tCarga0;
        System.out.printf("  Tiempo de carga    : %d ms%n%n", TIEMPO_CARGA_MS);

        List<EntradaRazonador> sinTimeout = Arrays.asList(
            new EntradaRazonador("HermiT", new ReasonerFactory())
        );
        List<EntradaRazonador> conTimeout = Arrays.asList(
            new EntradaRazonador("Openllet (Pellet)", OpenlletReasonerFactory.getInstance()),
            new EntradaRazonador("JFact (FaCT++)", new JFactFactory())
        );

        List<ResultadoBenchmark> resultados = new ArrayList<>();

        for (EntradaRazonador entrada : sinTimeout) {
            resultados.add(ejecutarBenchmark(entrada, ontologia));
        }

        for (EntradaRazonador entrada : conTimeout) {
            ExecutorService executor = Executors.newSingleThreadExecutor(r -> {
                Thread t = new Thread(r, "razonador-" + entrada.nombre);
                t.setDaemon(true);
                return t;
            });
            Future<ResultadoBenchmark> future = executor.submit(
                () -> ejecutarBenchmark(entrada, ontologia)
            );
            try {
                ResultadoBenchmark r = future.get(TIMEOUT_SEGUNDOS, TimeUnit.SECONDS);
                resultados.add(r);
            } catch (TimeoutException e) {
                future.cancel(true);
                System.out.println(RED + BOLD
                    + "\n[ " + entrada.nombre + " ] TIMEOUT - el razonador no logro clasificar en el tiempo limite."
                    + RESET + "\n");
                ResultadoBenchmark timeout = new ResultadoBenchmark(entrada.nombre);
                timeout.error = "TIMEOUT";
                resultados.add(timeout);
            } catch (InterruptedException | ExecutionException e) {
                future.cancel(true);
                ResultadoBenchmark err = new ResultadoBenchmark(entrada.nombre);
                err.error = e.getCause() != null ? e.getCause().getMessage() : e.getMessage();
                resultados.add(err);
            } finally {
                executor.shutdownNow();
            }
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
     * Se llama una única vez desde {@code main()}, y la ontología resultante
     * se comparte entre los tres razonadores (HermiT, Openllet, JFact), evitando
     * releer el TTL desde disco en cada benchmark. Libera explícitamente las
     * ontologías intermedias (base e instancias) una vez copiados sus axiomas
     * a {@code merged}.
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
     * La ontología se carga una única vez en {@code main()} y se comparte entre
     * los tres razonadores (ver {@link #cargarOntologias()}), por lo que aquí
     * solo se miden la inicialización del razonador y la precomputación de
     * inferencias. Si el razonador falla o la ontología es inconsistente, el
     * error queda registrado en {@link ResultadoBenchmark#error} y el método
     * retorna igualmente sin lanzar excepción.
     *
     * @param entrada par (nombre, factory) que identifica al razonador.
     * @param ontologia ontología fusionada, ya cargada una única vez en {@code main()}.
     * @return resultado con todas las métricas medidas, o con {@code error} no nulo si falló.
     */
    private static ResultadoBenchmark ejecutarBenchmark(EntradaRazonador entrada, OWLOntology ontologia) {

        System.out.println(BOLD + "\n[ " + entrada.nombre + " ]" + RESET);
        ResultadoBenchmark res = new ResultadoBenchmark(entrada.nombre);
        res.tiempoCargaMs = TIEMPO_CARGA_MS;

        OWLReasoner reasoner = null;

        try {
            System.gc();
            List<MemoryPoolMXBean> poolsHeap = new ArrayList<>();
            for (MemoryPoolMXBean pool : ManagementFactory.getMemoryPoolMXBeans()) {
                if (pool.getType() == MemoryType.HEAP) {
                    try {
                        pool.resetPeakUsage();
                        poolsHeap.add(pool);
                    } catch (UnsupportedOperationException ignored) {
                        // Este pool no soporta seguimiento de pico; se omite.
                    }
                }
            }

            OWLDataFactory factory = ontologia.getOWLOntologyManager().getOWLDataFactory();

            long t0 = System.currentTimeMillis();
            reasoner = entrada.factory.createReasoner(
                ontologia, new SimpleConfiguration(new MonitorProgreso(entrada.nombre))
            );
            long tInit = System.currentTimeMillis() - t0;
            res.tiempoInicMs = tInit;

            long t1 = System.currentTimeMillis();

            reasoner.precomputeInferences(
                InferenceType.CLASS_HIERARCHY,
                InferenceType.CLASS_ASSERTIONS
            );

            long tPrecomp = System.currentTimeMillis() - t1;
            res.tiempoPrecompMs = tPrecomp;
            res.tiempoTotalMs = tInit + tPrecomp;

            res.consistente = reasoner.isConsistent();
            System.out.printf("  Consistencia      : %s%n",
                res.consistente ? GREEN + "CONSISTENTE" + RESET : RED + "INCONSISTENTE" + RESET);

            long memPicoMB = 0;
            for (MemoryPoolMXBean pool : poolsHeap) {
                memPicoMB += pool.getPeakUsage().getUsed();
            }
            memPicoMB /= (1024 * 1024);
            res.memPicoMB = memPicoMB;

            if (!res.consistente) {
                return res;
            }

            res.numClasesJerarquia = reasoner
                .getSubClasses(factory.getOWLThing(), false)
                .getFlattened().size();

            Map<String, List<String>> tiposPorIndividuo = new LinkedHashMap<>();

            long totalInferencias = 0;
            for (String nombreClase : CLASES_MANO) {
                OWLClass clase = factory.getOWLClass(IRI.create(BASE_IRI + nombreClase));
                NodeSet<OWLNamedIndividual> instancias =
                    reasoner.getInstances(clase, false);
                Set<OWLNamedIndividual> planas = instancias.getFlattened();
                res.instanciasPorClase.put(nombreClase, planas.size());
                totalInferencias += planas.size();

                for (OWLNamedIndividual ind : planas) {
                    tiposPorIndividuo
                        .computeIfAbsent(ind.getIRI().getShortForm(), k -> new ArrayList<>())
                        .add(nombreClase);
                }
            }
            res.totalInferencias = totalInferencias;

            OWLClass manoClass = factory.getOWLClass(IRI.create(BASE_IRI + "Mano"));
            NodeSet<OWLNamedIndividual> todasManos =
                reasoner.getInstances(manoClass, false);

            System.out.println("  Inferencias en tiempo real:");
            for (OWLNamedIndividual ind : todasManos.getFlattened()) {
                String nombreInd = ind.getIRI().getShortForm();
                List<String> tiposNombre =
                    tiposPorIndividuo.getOrDefault(nombreInd, Collections.emptyList());
                System.out.printf("  " + YELLOW + "%-8s" + RESET + " : %s%n",
                    nombreInd,
                    tiposNombre.isEmpty()
                        ? RED + "(sin clase inferida)" + RESET
                        : GREEN + String.join(", ", tiposNombre) + RESET
                );
                res.clasificacionIndividual.put(nombreInd, tiposNombre);
            }
            System.out.println();

            System.out.printf("  %-22s : %d ms%n",  "Init",                tInit);
            System.out.printf("  %-22s : %d ms%n",  "Precomputacion",      tPrecomp);
            System.out.printf("  %-22s : %d ms%n",  "Total (init+precomp)", res.tiempoTotalMs);
            System.out.printf("  %-22s : %d MB%n",  "Memoria pico (real)", res.memPicoMB);
            System.out.printf("  %-22s : %d%n",     "Clases inferidas",    res.numClasesJerarquia);
            System.out.printf("  %-22s : %d%n%n",   "Inferencias totales", res.totalInferencias);

        } catch (Exception e) {
            res.error = e.getMessage();
            System.out.println(RED + "  [ERROR] " + e.getMessage() + RESET + "\n");
        } finally {
            if (reasoner != null) {
                reasoner.dispose();
            }
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

        String fmt = "%-22s │ %10s │ %10s │ %12s │ %10s │ %11s │ %8s │ %12s%n";
        System.out.printf(BOLD + fmt + RESET,
            "Razonador", "Carga (ms)", "Init (ms)", "Precomp (ms)", "Total (ms)",
            "Mem pico(MB)", "Consist.", "Inferencias");
        System.out.println("─".repeat(109));

        for (ResultadoBenchmark r : resultados) {
            if (r.error != null) {
                String etiqueta = "TIMEOUT".equals(r.error) ? "TIMEOUT" : "ERROR: " + r.error;
                // Se rellena cada celda al ancho correcto ANTES de agregar los códigos
                // de color, para que las secuencias ANSI no cuenten como caracteres
                // visibles y desalineen las columnas.
                String c10 = RED + String.format("%10s", etiqueta) + RESET;
                String c12 = RED + String.format("%12s", etiqueta) + RESET;
                String c11 = RED + String.format("%11s", etiqueta) + RESET;
                String c8  = RED + String.format("%8s",  etiqueta) + RESET;
                System.out.printf("%-22s │ %s │ %s │ %s │ %s │ %s │ %s │ %s%n",
                    r.nombre, c10, c10, c12, c10, c11, c8, c12);
                continue;
            }
            System.out.printf(fmt,
                r.nombre,
                r.tiempoCargaMs,
                r.tiempoInicMs,
                r.tiempoPrecompMs,
                r.tiempoTotalMs,
                r.memPicoMB,
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
                    String texto = String.valueOf(n);
                    if (n > 0) {
                        fila.append(" │ ").append(GREEN)
                            .append(String.format("%-" + colRazon + "s", texto))
                            .append(RESET);
                    } else {
                        fila.append(String.format(" │ %-" + colRazon + "s", texto));
                    }
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
            System.out.printf(BOLD + "  %-8s" + RESET, ind);
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
            .min(Comparator.comparingLong(r -> r.memPicoMB))
            .orElse(null);
        if (menosMem != null) {
            System.out.println(GREEN + BOLD
                + "  Menor consumo de memoria: " + menosMem.nombre
                + " (" + menosMem.memPicoMB + " MB pico)" + RESET);
        }
        System.out.println();
    }

    /**
     * Detecta el tipo de mano a partir del nombre del archivo de instancias,
     * mirando si termina en "_<tipo>" (ej: instancias_baraja_6r_4p_par.ttl -> "par").
     * Si no coincide con ningún tipo conocido, se asume que el archivo contiene
     * todas las manos juntas y devuelve "todas".
     *
     * @param rutaInstancias ruta al archivo .ttl de instancias (INST_TTL).
     * @return el tipo de mano detectado, o "todas" si no se pudo determinar.
     */
    private static String detectarTipoMano(String rutaInstancias) {
        String nombreBase = Paths.get(rutaInstancias).getFileName().toString()
            .replaceAll("\\.ttl$", "");
        for (String tipo : TIPOS_MANO_ARCHIVO) {
            if (nombreBase.endsWith("_" + tipo)) {
                return tipo;
            }
        }
        return "todas";
    }

    /**
     * Genera un único archivo CSV con dos secciones:
     * resumen de métricas por razonador y clasificación individual.
     *
     * @param resultados lista de resultados, uno por razonador.
     */
    private static void guardarCSV(List<ResultadoBenchmark> resultados) {

        String variante = Paths.get(BASE_TTL).getFileName().toString()
            .replaceAll("\\.ttl$", "");
        String tipoMano = detectarTipoMano(INST_TTL);

        Path dirPath = Paths.get(RESULTADOS_DIR);
        try {
            Files.createDirectories(dirPath);
        } catch (IOException e) {
            System.err.println(RED + "[CSV] No se pudo crear " + dirPath.toAbsolutePath()
                + ": " + e.getMessage() + RESET);
            return;
        }

        String nombre = variante + "_" + tipoMano + "_benchmark_" + TIMESTAMP + ".csv";
        Path archivo = dirPath.resolve(nombre);

        try (PrintWriter pw = new PrintWriter(
                new OutputStreamWriter(
                    new FileOutputStream(archivo.toFile()), StandardCharsets.UTF_8))) {

            pw.println("# RESUMEN DE METRICAS POR RAZONADOR");

            StringBuilder cabecera1 = new StringBuilder(
                "variante,razonador,carga_ms,init_ms,precomp_ms,total_ms," +
                "mem_pico_mb," +
                "consistente,clases_jerarquia,total_inferencias");
            for (String c : CLASES_MANO) cabecera1.append(",inst_").append(c);
            pw.println(cabecera1);

            for (ResultadoBenchmark r : resultados) {
                if (r.error != null) {
                    String t = csvEscape(r.error);
                    StringBuilder fila = new StringBuilder();
                    fila.append(csvEscape(variante)).append(',');
                    fila.append(csvEscape(r.nombre));
                    int totalCampos = 8 + CLASES_MANO.length;
                    for (int i = 0; i < totalCampos; i++) fila.append(',').append(t);
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
                fila.append(r.memPicoMB).append(',');
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

    /**
     * Reporta el avance del razonador durante {@code precomputeInferences()}.
     *
     * La OWL API invoca estos callbacks desde dentro del propio algoritmo del
     * razonador: {@code reasonerTaskStarted}/{@code reasonerTaskStopped} delimitan
     * cada fase (p.ej. "Computing class hierarchy"), y {@code reasonerTaskProgressChanged}
     * reporta un porcentaje dentro de esa fase. No es un contador de inferencias en
     * tiempo real (eso no lo expone ningún razonador OWL) sino un indicador de avance
     * por fase del algoritmo.
     */
    static class MonitorProgreso implements ReasonerProgressMonitor {

        private static final long INTERVALO_BUSY_MS = 5_000;

        /**
         * Nombres de tarea que los propios razonadores (HermiT, Openllet, JFact)
         * pasan hardcodeados en inglés a reasonerTaskStarted(). No los generamos
         * nosotros: solo los traducimos acá para que la consola quede en español.
         * Si aparece un nombre de tarea nuevo (otra fase, otro razonador), se
         * imprime tal cual y hay que agregarlo a este mapa.
         */
        private static final Map<String, String> TRADUCCIONES_TAREA = Map.of(
            "Building the class hierarchy...", "Construyendo la jerarquía de clases...",
            "Initializing class instance data structures", "Inicializando estructuras de datos de instancias",
            "Classifying", "Clasificando",
            "Loading", "Cargando"
        );

        private static String traducir(String taskName) {
            String traducido = TRADUCCIONES_TAREA.getOrDefault(taskName, taskName);
            return traducido.replaceAll("\\.+$", "");
        }

        private final String nombreRazonador;
        private String tareaActual = "";
        private long tInicioTarea;
        private int ultimoPorcentajeImpreso;
        private long ultimoBusyImpreso;

        MonitorProgreso(String nombreRazonador) {
            this.nombreRazonador = nombreRazonador;
        }

        @Override
        public void reasonerTaskStarted(String taskName) {
            tareaActual = traducir(taskName);
            tInicioTarea = System.currentTimeMillis();
            ultimoPorcentajeImpreso = -1;
            ultimoBusyImpreso = 0;
            System.out.printf("  " + CYAN + "[%s] > %s..." + RESET + "%n",
                nombreRazonador, tareaActual);
        }

        @Override
        public void reasonerTaskStopped() {
            long transcurridoMs = System.currentTimeMillis() - tInicioTarea;
            System.out.printf("  " + CYAN + "[%s] < %s completado (%d ms)" + RESET + "%n",
                nombreRazonador, tareaActual, transcurridoMs);
        }

        @Override
        public void reasonerTaskProgressChanged(int value, int max) {
            if (max <= 0) return;
            int porcentaje = (int) ((value * 100L) / max);
            // Imprime cada 10 puntos porcentuales como mínimo, para no saturar la consola
            // en ontologías con jerarquías grandes.
            if (porcentaje >= ultimoPorcentajeImpreso + 10 || porcentaje == 100) {
                ultimoPorcentajeImpreso = porcentaje;
                long transcurridoMs = System.currentTimeMillis() - tInicioTarea;
                System.out.printf("  [%s] %-14s : %3d%%  (%d/%d)  [%d ms]%n",
                    nombreRazonador, tareaActual, porcentaje, value, max, transcurridoMs);
            }
        }

        @Override
        public void reasonerTaskBusy() {
            long ahora = System.currentTimeMillis();
            if (ahora - ultimoBusyImpreso >= INTERVALO_BUSY_MS) {
                ultimoBusyImpreso = ahora;
                long transcurridoMs = ahora - tInicioTarea;
                System.out.printf("  " + YELLOW + "[%s] %-14s : ocupado... [%d ms transcurridos]" + RESET + "%n",
                    nombreRazonador, tareaActual, transcurridoMs);
            }
        }
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
        long memPicoMB = 0;
        boolean consistente = false;
        long numClasesJerarquia = 0;
        long totalInferencias = 0;
        String error = null;
        Map<String, Integer>      instanciasPorClase    = new LinkedHashMap<>();
        Map<String, List<String>> clasificacionIndividual = new LinkedHashMap<>();

        ResultadoBenchmark(String nombre) { this.nombre = nombre; }
    }
}