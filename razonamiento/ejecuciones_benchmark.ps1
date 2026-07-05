<#
.SYNOPSIS
    Ejecuta BenchmarkOWLDefinitivo una vez por cada archivo de instancias de una
    carpeta (por ejemplo, los 10 archivos divididos por tipo de mano), usando
    siempre la misma ontología base, en ejecuciones separadas y seguidas.

.PARAMETER OntologiaBase
    Ruta al archivo .ttl de la ontología base.

.PARAMETER CarpetaInstancias
    Carpeta que contiene los archivos de instancias .ttl a ejecutar
    (uno por tipo de mano, por ejemplo).

.PARAMETER Jar
    Ruta al .jar del benchmark. Por defecto usa la misma ruta relativa que
    venías usando manualmente.

.PARAMETER CarpetaLogs
    Carpeta donde se guarda una copia de la salida de consola de cada
    ejecución (un .txt por archivo de instancias). Se crea si no existe.

.EXAMPLE
    .\ejecutar_benchmarks.ps1 `
        -OntologiaBase ..\ontologias\ontologias_customizadas\barajas_6_rangos\baraja_6r_4p.ttl `
        -CarpetaInstancias ..\instancias\instancias_divididas\instancias_barajas_6_rangos
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$OntologiaBase,

    [Parameter(Mandatory = $true)]
    [string]$CarpetaInstancias,

    [string]$Jar = "target/poker-reasoner-1.0-SNAPSHOT-jar-with-dependencies.jar",

    [string]$CarpetaLogs = "..\resultados\logs"
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

# Sin esto, al pasar la salida de Java por una tuberia (|), PowerShell puede
# decodificarla con una codificacion distinta a UTF-8 y los caracteres de las
# cajas (║ ═ │ etc.) se muestran como "?". Se fuerza UTF-8 tanto en la consola
# como en la propia JVM para que todo quede consistente.
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 > $null

# Se ordenan alfabeticamente para que las 10 ejecuciones salgan siempre en el
# mismo orden (carta_alta, color, doblepar, escalera, escalera_color, ...).
$archivosInstancias = Get-ChildItem -Path $CarpetaInstancias -Filter "*.ttl" | Sort-Object Name

if ($archivosInstancias.Count -eq 0) {
    Write-Error "No se encontraron archivos .ttl en: $CarpetaInstancias"
    exit 1
}

New-Item -ItemType Directory -Force -Path $CarpetaLogs | Out-Null

Write-Host ""
Write-Host "Se van a ejecutar $($archivosInstancias.Count) benchmarks (uno por archivo de instancias)."
Write-Host "Ontologia base : $OntologiaBase"
Write-Host "Carpeta logs   : $CarpetaLogs"
Write-Host ""

$numero = 0
foreach ($archivo in $archivosInstancias) {
    $numero++

    Write-Host "==================================================================="
    Write-Host " [$numero/$($archivosInstancias.Count)] $($archivo.Name)"
    Write-Host "==================================================================="

    $logFile = Join-Path $CarpetaLogs ("$($archivo.BaseName)_log.txt")

    & java -Xms30g -Xmx32g "-Dstdout.encoding=UTF-8" "-Dfile.encoding=UTF-8" `
        -cp $Jar poker.BenchmarkOWLDefinitivo `
        $OntologiaBase $archivo.FullName 2>&1 | Tee-Object -FilePath $logFile

    Write-Host ""
}

Write-Host "Listo: se ejecutaron $numero benchmarks."
Write-Host "Logs de consola guardados en: $CarpetaLogs"
Write-Host "Los CSV de cada corrida quedaron donde los guarda siempre BenchmarkOWLDefinitivo (..\resultados)."