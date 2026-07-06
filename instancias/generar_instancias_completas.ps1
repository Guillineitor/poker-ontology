<#
.SYNOPSIS
    Ejecuta generador_instancias.py una vez por cada ontologia .ttl encontrada
    dentro de la carpeta ontologias_customizadas, y guarda cada
    instancias_*.ttl resultante en una carpeta paralela que refleja la misma
    estructura de subcarpetas (barajas_<N>_rangos).

.PARAMETER ScriptInstancias
    Ruta al script generador_instancias.py.

.PARAMETER CarpetaOntologias
    Carpeta raiz donde buscar los .ttl de las barajas
    customizadas a procesar.

.PARAMETER CarpetaSalida
    Carpeta raiz donde se guardan los instancias_*.ttl generados, replicando
    la misma estructura de subcarpetas que CarpetaOntologias.

.PARAMETER PythonExe
    Ejecutable de Python a usar.

.PARAMETER Filtro
    Patron de nombre de archivo a procesar. Por defecto
    procesa todos los .ttl encontrados.

.PARAMETER Forzar
    Si se indica, regenera instancias aunque el archivo de salida ya exista.
    Por defecto se omiten los que ya tienen su instancias_*.ttl (la generacion
    usa random, asi que no se pisan resultados existentes sin pedirlo explicitamente).

.PARAMETER SoloListar
    Si se indica, solo lista que .ttl se procesarian y donde quedaria cada
    salida, sin ejecutar nada.

.EXAMPLE
    # Desde la carpeta instancias\, procesa las 24 ontologias customizadas:
    .\generar_instancias_completas.ps1

.EXAMPLE
    # Revisar que se haria sin ejecutar nada:
    .\generar_instancias_completas.ps1 -SoloListar

.EXAMPLE
    # Generar instancias de solo ontologías con barajas customizadas de cierto de rango:
    .\generar_instancias_completas.ps1 -Filtro "baraja_6r_*"

.EXAMPLE
    # Regenerar todo de nuevo aunque ya existan instancias:
    .\generar_instancias_completas.ps1 -Forzar
#>

param(
    [string]$ScriptInstancias = ".\generador_instancias_completas.py",
    [string]$CarpetaOntologias = "..\ontologias\ontologias_customizadas",
    [string]$CarpetaSalida = "..\instancias\instancias_completas",
    [string]$PythonExe = "python",
    [string]$Filtro = "*.ttl",
    [switch]$Forzar,
    [switch]$SoloListar
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
Write-Host "Se encontraron $($archivos.Count) ontologias para procesar."
if ($SoloListar) { Write-Host "(-SoloListar activo: no se ejecutara nada, solo se lista)" }
Write-Host ""

$numero = 0
$generados = 0
$omitidos = 0
$fallidos = 0
$tInicioTotal = Get-Date

foreach ($archivo in $archivos) {
    $numero++

    $subcarpetaRelativa = $archivo.DirectoryName.Substring($ontologiasAbsoluto.Length).Trim('\', '/')

    $nombreBase = [System.IO.Path]::GetFileNameWithoutExtension($archivo.Name)
    $carpetaDestino = if ($subcarpetaRelativa) { Join-Path $CarpetaSalida "instancias_$subcarpetaRelativa" } else { $CarpetaSalida }
    $archivoDestino = Join-Path $carpetaDestino "instancias_$nombreBase.ttl"

    Write-Host "[$numero/$($archivos.Count)] $($archivo.Name)"

    if ((Test-Path $archivoDestino) -and (-not $Forzar)) {
        Write-Host "  Ya existe, se omite (usa -Forzar para regenerar): $archivoDestino"
        $omitidos++
        Write-Host ""
        continue
    }

    if ($SoloListar) {
        Write-Host "  Se generaria en: $archivoDestino"
        Write-Host ""
        continue
    }

    New-Item -ItemType Directory -Force -Path $carpetaDestino | Out-Null

    Push-Location $carpetaDestino
    try {
        & $PythonExe $scriptAbsoluto $archivo.FullName
        $codigoSalida = $LASTEXITCODE
    } finally {
        Pop-Location
    }

    if ($codigoSalida -ne 0) {
        Write-Warning "  generador_instancias_completas.py devolvio codigo $codigoSalida para $($archivo.Name)."
        $fallidos++
    } elseif (Test-Path $archivoDestino) {
        Write-Host "  Generado: $archivoDestino"
        $generados++
    } else {
        Write-Warning "  No se encontro el archivo esperado: $archivoDestino"
        $fallidos++
    }

    Write-Host ""
}

$duracionTotal = (Get-Date) - $tInicioTotal

if ($SoloListar) {
    Write-Host "Listado terminado. Se procesarian $($archivos.Count) archivos."
} else {
    Write-Host "Proceso terminado. Se generaron $generados instancias (de $($archivos.Count) ontologias) en $([math]::Round($duracionTotal.TotalSeconds, 1)) s."
    if ($omitidos -gt 0) { Write-Host "  Omitidos (ya existian): $omitidos" }
    if ($fallidos -gt 0) { Write-Host "  Fallidos: $fallidos" }
    Write-Host "Organizadas en subcarpetas instancias_barajas_<N>_rangos dentro de: $CarpetaSalida"
}