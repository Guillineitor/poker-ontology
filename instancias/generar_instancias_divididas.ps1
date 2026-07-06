<#
.SYNOPSIS
    Ejecuta generador_instancias_divididas.py una vez por cada ontologia .ttl
    encontrada dentro de ontologias_customizadas. A diferencia de
    generar_instancias_completas.ps1, cada ejecución produce 10 archivos (uno por
    tipo de mano, 4 manos) en vez de 1 archivos y 40 manos, asi que cada baraja recibe su propia subcarpeta:

        CarpetaSalida\instancias_barajas_<N>_rangos\<nombre_baraja>\instancias_<nombre_baraja>_<tipo>.ttl

.PARAMETER ScriptInstancias
    Ruta al script generador_instancias_divididas.py.

.PARAMETER CarpetaOntologias
    Carpeta raiz donde buscar los .ttl de las barajas
    customizadas a procesar.

.PARAMETER CarpetaSalida
    Carpeta raiz donde se guardan los archivos generados, replicando la misma
    estructura de subcarpetas que CarpetaOntologias, mas una subcarpeta extra
    por baraja (ya que cada una produce 10 archivos, uno por tipo de mano).

.PARAMETER PythonExe
    Ejecutable de Python a usar.

.PARAMETER Filtro
    Patron de nombre de archivo a procesar. Por defecto procesa todos los .ttl
    encontrados.

.PARAMETER Forzar
    Si se indica, regenera instancias aunque ya existan los 10 archivos de esa
    baraja.

.PARAMETER SoloListar
    Si se indica, solo lista que .ttl se procesarian y donde quedaria cada
    salida, sin ejecutar nada.

.EXAMPLE
    # Desde la carpeta instancias\, procesa las 24 ontologias customizadas:
    .\generar_instancias_divididas.ps1

.EXAMPLE
    # Revisar que se haria sin ejecutar nada:
    .\generar_instancias_divididas.ps1 -SoloListar

.EXAMPLE
    # Generar instancias de solo ontologías con barajas customizadas de cierto de rango:
    .\generar_instancias_divididas.ps1 -Filtro "baraja_6r_*"

.EXAMPLE
    # Regenerar todo de nuevo aunque ya existan instancias:
    .\generar_instancias_divididas.ps1 -Forzar
#>

param(
    [string]$ScriptInstancias = ".\generador_instancias_divididas.py",
    [string]$CarpetaOntologias = "..\ontologias\ontologias_customizadas",
    [string]$CarpetaSalida = "..\instancias\instancias_divididas",
    [string]$PythonExe = "python",
    [string]$Filtro = "*.ttl",
    [switch]$Forzar,
    [switch]$SoloListar
)

$tiposMano = @(
    "carta_alta", "par", "doble_par", "trio", "escalera",
    "color", "full", "poker", "escalera_color", "escalera_real"
)

if (-not (Test-Path $ScriptInstancias)) {
    Write-Error "No se encontro el script generador: $ScriptInstancias"
    exit 1
}
if (-not (Test-Path $CarpetaOntologias)) {
    Write-Error "No se encontro la carpeta de ontologias: $CarpetaOntologias"
    exit 1
}

$scriptAbsoluto = (Resolve-Path $ScriptInstancias).Path
$ontologiasAbsoluto = (Resolve-Path $CarpetaOntologias).Path

$archivos = Get-ChildItem -Path $ontologiasAbsoluto -Recurse -Filter $Filtro | Sort-Object FullName

if ($archivos.Count -eq 0) {
    Write-Warning "No se encontraron archivos .ttl en $ontologiasAbsoluto con el filtro '$Filtro'."
    exit 0
}

Write-Host ""
Write-Host "Se encontraron $($archivos.Count) ontologias para procesar ($($tiposMano.Count) archivos cada una)."
if ($SoloListar) { Write-Host "(-SoloListar activo: no se ejecutara nada, solo se lista)" }
Write-Host ""

$numero = 0
$barajasGeneradas = 0
$omitidas = 0
$fallidas = 0
$tInicioTotal = Get-Date

foreach ($archivo in $archivos) {
    $numero++

    $subcarpetaRelativa = $archivo.DirectoryName.Substring($ontologiasAbsoluto.Length).Trim('\', '/')
    $nombreBase = [System.IO.Path]::GetFileNameWithoutExtension($archivo.Name)

    $carpetaGrupo = if ($subcarpetaRelativa) { Join-Path $CarpetaSalida "instancias_$subcarpetaRelativa" } else { $CarpetaSalida }
    $carpetaBaraja = Join-Path $carpetaGrupo $nombreBase

    $archivosEsperados = $tiposMano | ForEach-Object { Join-Path $carpetaBaraja "instancias_${nombreBase}_$_.ttl" }
    $completo = -not ($archivosEsperados | Where-Object { -not (Test-Path $_) })

    Write-Host "[$numero/$($archivos.Count)] $($archivo.Name)"

    if ($completo -and (-not $Forzar)) {
        Write-Host "  Ya existen los $($tiposMano.Count) archivos, se omite (usa -Forzar para regenerar): $carpetaBaraja"
        $omitidas++
        Write-Host ""
        continue
    }

    if ($SoloListar) {
        Write-Host "  Se generarian $($tiposMano.Count) archivos en: $carpetaBaraja"
        Write-Host ""
        continue
    }

    New-Item -ItemType Directory -Force -Path $carpetaBaraja | Out-Null

    Push-Location $carpetaBaraja
    try {
        & $PythonExe $scriptAbsoluto $archivo.FullName
        $codigoSalida = $LASTEXITCODE
    } finally {
        Pop-Location
    }

    $completoAhora = -not ($archivosEsperados | Where-Object { -not (Test-Path $_) })

    if ($codigoSalida -ne 0) {
        Write-Warning "  generador_instancias_divididas.py devolvio codigo $codigoSalida para $($archivo.Name)."
        $fallidas++
    } elseif ($completoAhora) {
        Write-Host "  Generados los $($tiposMano.Count) archivos en: $carpetaBaraja"
        $barajasGeneradas++
    } else {
        $faltantes = ($archivosEsperados | Where-Object { -not (Test-Path $_) }).Count
        Write-Warning "  Faltan $faltantes de $($tiposMano.Count) archivos esperados en: $carpetaBaraja"
        $fallidas++
    }

    Write-Host ""
}

$duracionTotal = (Get-Date) - $tInicioTotal

if ($SoloListar) {
    Write-Host "Listado terminado. Se procesarian $($archivos.Count) ontologias ($($archivos.Count * $tiposMano.Count) archivos en total)."
} else {
    Write-Host "Proceso terminado. Se generaron instancias divididas para $barajasGeneradas barajas (de $($archivos.Count)), $($barajasGeneradas * $tiposMano.Count) archivos en total, en $([math]::Round($duracionTotal.TotalSeconds, 1)) s."
    if ($omitidas -gt 0) { Write-Host "  Omitidas (ya existian): $omitidas" }
    if ($fallidas -gt 0) { Write-Host "  Fallidas: $fallidas" }
    Write-Host "Organizadas en subcarpetas instancias_barajas_<N>_rangos\<nombre_baraja> dentro de: $CarpetaSalida"
}