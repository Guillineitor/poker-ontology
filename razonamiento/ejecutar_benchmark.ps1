<#
.SYNOPSIS
    Ejecuta BenchmarkOWLDefinitivo una vez por cada archivo de instancias de una
    carpeta (por ejemplo, los 10 archivos divididos por tipo de mano), usando
    siempre la misma ontología base, en ejecuciones separadas y seguidas.
    Despues de cada corrida, los .csv recien creados se mueven a una subcarpeta propia de
    esa ontología: ..\resultados\resultado_<nombre_ontologia> .

    El orden de ejecucion sigue la jerarquia de manos de poker (de menor a
    mayor valor): carta_alta, par, doblepar, trio, escalera, color, full,
    poker, escalera_color, escalera_real. No es alfabetico.

.PARAMETER OntologiaBase
    Ruta al archivo .ttl de la ontología base.

.PARAMETER CarpetaInstancias
    Carpeta que contiene los archivos de instancias .ttl a ejecutar.

.PARAMETER Jar
    Ruta al .jar del benchmark. 

.PARAMETER CarpetaResultados
    Carpeta donde BenchmarkOWLDefinitivo guarda los .csv. Por defecto "..\resultados".

.EXAMPLE
    .\ejecutar_benchmark.ps1 `
        -OntologiaBase ..\ontologias\ontologias_customizadas\barajas_6_rangos\baraja_6r_4p.ttl `
        -CarpetaInstancias ..\instancias\instancias_divididas\instancias_barajas_6_rangos
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$OntologiaBase,

    [Parameter(Mandatory = $true)]
    [string]$CarpetaInstancias,

    [string]$Jar = "target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar",

    [string]$CarpetaResultados = "..\resultados"
)

if (-not (Test-Path $OntologiaBase)) {
    Write-Error "No se encontro la ontologia base: $OntologiaBase"
    exit 1
}
if (-not (Test-Path $CarpetaInstancias)) {
    Write-Error "No se encontro la carpeta de instancias: $CarpetaInstancias"
    exit 1
}
if (-not (Test-Path $Jar)) {
    Write-Error "No se encontro el .jar del benchmark: $Jar"
    exit 1
}

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 > $null

$ordenTipos = @(
    "carta_alta", "par", "doblepar", "trio", "escalera",
    "color", "full", "poker", "escalera_color", "escalera_real"
)
$indicePorTipo = @{}
for ($i = 0; $i -lt $ordenTipos.Count; $i++) { $indicePorTipo[$ordenTipos[$i]] = $i }

$tiposPorLongitud = $ordenTipos | Sort-Object Length -Descending

function Obtener-IndiceJerarquia([string]$nombreBase) {
    foreach ($tipo in $tiposPorLongitud) {
        if ($nombreBase -like "*_$tipo") {
            return $indicePorTipo[$tipo]
        }
    }
    return 999   
}

$archivosInstancias = Get-ChildItem -Path $CarpetaInstancias -Filter "*.ttl" |
    Sort-Object { Obtener-IndiceJerarquia $_.BaseName }, Name

if ($archivosInstancias.Count -eq 0) {
    Write-Error "No se encontraron archivos .ttl en: $CarpetaInstancias"
    exit 1
}

$nombreOntologia = [System.IO.Path]::GetFileNameWithoutExtension($OntologiaBase)
$carpetaDestino = Join-Path $CarpetaResultados ("resultado_$nombreOntologia")
New-Item -ItemType Directory -Force -Path $carpetaDestino | Out-Null

$patronCsv = $nombreOntologia + "_*_benchmark_*.csv"

Write-Host ""
Write-Host "Se van a ejecutar $($archivosInstancias.Count) benchmarks (uno por archivo de instancias)."
Write-Host "Ontologia base : $OntologiaBase"
Write-Host "Carpeta resultados: $carpetaDestino"
Write-Host ""

$numero = 0
foreach ($archivo in $archivosInstancias) {
    $numero++

    Write-Host "==================================================================="
    Write-Host " [$numero/$($archivosInstancias.Count)] $($archivo.Name)"
    Write-Host "==================================================================="

    $tInicio = Get-Date

    & java -Xms30g -Xmx32g "-Dstdout.encoding=UTF-8" "-Dfile.encoding=UTF-8" `
        -cp $Jar poker.BenchmarkOWLDefinitivo `
        $OntologiaBase $archivo.FullName

    $csvNuevo = Get-ChildItem -Path $CarpetaResultados -File -Filter $patronCsv -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -ge $tInicio } |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1

    if ($csvNuevo) {
        Move-Item -Path $csvNuevo.FullName -Destination $carpetaDestino -Force
        Write-Host "  CSV movido a: $(Join-Path $carpetaDestino $csvNuevo.Name)"
    } else {
        Write-Warning "  No se encontro el CSV generado para $($archivo.Name) en $CarpetaResultados"
    }

    Write-Host ""
}

Write-Host "Proceso terminado. Se ejecutaron $numero benchmarks."
Write-Host "Los CSV de todas las ejecuciones fueron guardados en: $carpetaDestino"