<#
.SYNOPSIS
    Ejecuta generador_ontologias.py una vez por cada combinación de (rangos, palos)
    de la matriz de pruebas del benchmark, y organiza cada .ttl generado dentro de
    una carpeta "barajas_<N>_rangos" según su cantidad de rangos.

    generador_ontologias.py es interactivo (usa input() tres veces: nombre, palos,
    rangos), así que este script le pasa las respuestas por stdin en vez de argumentos.
    generador_ontologias.py siempre escribe en <raiz_proyecto>\ontologias\ontologias_customizadas\
    (ruta calculada a partir de su propia ubicación en disco, sin importar desde
    dónde se invoque), así que -CarpetaSalida debe apuntar a esa misma carpeta.

.PARAMETER ScriptGenerador
    Ruta al script generador_ontologias.py.

.PARAMETER CarpetaSalida
    Carpeta donde generador_ontologias.py escribe los .ttl (ontologias_customizadas).
    Ahí mismo se crean las subcarpetas barajas_<N>_rangos.

.PARAMETER PythonExe
    Ejecutable de Python a usar.

.PARAMETER GruposRangos
    Cantidades de rangos a generar. Cada una crea su propia carpeta barajas_<N>_rangos.

.PARAMETER GruposPalos
    Cantidades de palos a generar dentro de cada grupo de rangos.

.PARAMETER SoloListar
    Si se indica, solo imprime las combinaciones que se generarían, sin ejecutar
    generador_ontologias.py ni tocar el disco. Útil para revisar antes de correr.

.EXAMPLE
    # Desde la carpeta generador_ontologias\, con los valores por defecto
    # (6/13/19/25/31/37 rangos x 4/8/12/16 palos = 24 archivos):
    .\generar_barajas.ps1

.EXAMPLE
    # Revisar qué se generaría sin escribir nada:
    .\generar_barajas.ps1 -SoloListar

.EXAMPLE
    # Solo la serie de 6 rangos:
    .\generar_barajas.ps1 -GruposRangos 6
#>

param(
    [string]$ScriptGenerador = ".\generador_ontologias.py",
    [string]$CarpetaSalida = "..\ontologias\ontologias_customizadas",
    [string]$PythonExe = "python",

    [int[]]$GruposRangos = @(6, 13, 19, 25, 31, 37),
    [int[]]$GruposPalos = @(4, 8, 12, 16),

    [switch]$SoloListar
)

$todosPalos = @(
    "Fuego", "Agua", "Planta", "Eléctrico", "Normal", "Volador", "Bicho", "Veneno",
    "Tierra", "Roca", "Lucha", "Psíquico", "Fantasma", "Hielo", "Dragón", "Siniestro"
)

$todosRangos = @(
    "Uno", "Dos", "Tres", "Cuatro", "Cinco", "Seis", "Siete", "Ocho", "Nueve", "Diez",
    "Once", "Doce", "Trece", "Catorce", "Quince", "Dieciseis", "Diecisiete", "Dieciocho", "Diecinueve",
    "Veinte", "Veintiuno", "Veintidos", "Veintitres", "Veinticuatro", "Veinticinco",
    "Veintiseis", "Veintisiete", "Veintiocho", "Veintinueve", "Treinta", "Treintayuno",
    "Treintaydos", "Treintaytres", "Treintaycuatro", "Treintaycinco", "Treintayseis", "Treintaysiete"
)

if (-not $SoloListar) {
    if (-not (Test-Path $ScriptGenerador)) {
        Write-Error "No se encontro el script generador: $ScriptGenerador"
        exit 1
    }
    New-Item -ItemType Directory -Force -Path $CarpetaSalida | Out-Null

    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    [Console]::InputEncoding  = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
    $env:PYTHONIOENCODING = "utf-8"
    chcp 65001 > $null
}

$maxRangoPedido = ($GruposRangos | Measure-Object -Maximum).Maximum
$maxPaloPedido  = ($GruposPalos  | Measure-Object -Maximum).Maximum
if ($maxRangoPedido -gt $todosRangos.Count) {
    Write-Error "Se pidieron hasta $maxRangoPedido rangos pero el catalogo solo tiene $($todosRangos.Count)."
    exit 1
}
if ($maxPaloPedido -gt $todosPalos.Count) {
    Write-Error "Se pidieron hasta $maxPaloPedido palos pero el catalogo solo tiene $($todosPalos.Count)."
    exit 1
}

$totalCombos = $GruposRangos.Count * $GruposPalos.Count
Write-Host ""
Write-Host "Se van a generar $totalCombos barajas ($($GruposRangos.Count) grupos de rangos x $($GruposPalos.Count) grupos de palos)."
if ($SoloListar) { Write-Host "(-SoloListar activo: no se ejecutara nada, solo se lista)" }
Write-Host ""

$numero = 0
$tInicioTotal = Get-Date

foreach ($nRangos in $GruposRangos) {

    $rangosGrupo  = $todosRangos[0..($nRangos - 1)]
    $carpetaGrupo = Join-Path $CarpetaSalida "barajas_${nRangos}_rangos"

    if (-not $SoloListar) {
        New-Item -ItemType Directory -Force -Path $carpetaGrupo | Out-Null
    }

    foreach ($nPalos in $GruposPalos) {
        $numero++

        $palosGrupo   = $todosPalos[0..($nPalos - 1)]
        $nombreBaraja = "baraja_${nRangos}r_${nPalos}p"
        $palosLinea   = $palosGrupo -join ", "
        $rangosLinea  = $rangosGrupo -join ", "

        Write-Host "==================================================================="
        Write-Host " [$numero/$totalCombos] $nombreBaraja  ($nPalos palos x $nRangos rangos)"
        Write-Host "==================================================================="

        if ($SoloListar) {
            Write-Host "  Palos  : $palosLinea"
            Write-Host "  Rangos : $rangosLinea"
            Write-Host ""
            continue
        }

        $tInicio = Get-Date

        $respuestas = @($nombreBaraja, $palosLinea, $rangosLinea)
        $respuestas | & $PythonExe $ScriptGenerador

        if ($LASTEXITCODE -ne 0) {
            Write-Warning "  generador_ontologias.py devolvio codigo $LASTEXITCODE para $nombreBaraja. Se omite."
            Write-Host ""
            continue
        }

        $archivoGenerado = Join-Path $CarpetaSalida "$nombreBaraja.ttl"

        if ((Test-Path $archivoGenerado) -and ((Get-Item $archivoGenerado).LastWriteTime -ge $tInicio)) {
            Move-Item -Path $archivoGenerado -Destination $carpetaGrupo -Force
            Write-Host "  Movido a: $(Join-Path $carpetaGrupo "$nombreBaraja.ttl")"
        } else {
            Write-Warning "  No se encontro el archivo esperado: $archivoGenerado"
        }

        Write-Host ""
    }
}

$duracionTotal = (Get-Date) - $tInicioTotal

if ($SoloListar) {
    Write-Host "Listado terminado. Se habrían generado $numero ontologías con barajas customizadas."
} else {
    Write-Host "Proceso terminado. Se generaron $numero ontologías con barajas customizadas en $([math]::Round($duracionTotal.TotalSeconds, 1)) s."
    Write-Host "Organizadas en subcarpetas barajas_<N>_rangos dentro de: $CarpetaSalida"
}