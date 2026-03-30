<#
.SYNOPSIS
Script para automatizar la instalacion de OpenJDK 17 en entornos Windows.
Requerido para la ejecucion del motor analitico PySpark en el pipeline.

.DESCRIPTION
Este script descarga OpenJDK 17 de Eclipse Temurin, lo extrae en el perfil del usuario
y configura la variable de entorno JAVA_HOME a nivel de Usuario,
agregandolo tambien al PATH para que PySpark pueda encontrar la JVM.
#>

param (
    [string]$InstallDir = "$env:USERPROFILE\.java"
)

# Forzar TLS 1.2 para descargar
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$DownloadUrl = "https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.10%2B7/OpenJDK17U-jdk_x64_windows_hotspot_17.0.10_7.zip"
$ZipPath = "$env:TEMP\openjdk17.zip"
$ExtractDir = "$InstallDir\jdk-17"

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "INSTALADOR AUTOMÁTICO - DEPENDENCIAS DE PYSPARK" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "Verificando instalación de Java..."

$JavaExists = Get-Command "java" -ErrorAction SilentlyContinue
if ($JavaExists -and $env:JAVA_HOME) {
    Write-Host "Java parece estar instalado. JAVA_HOME=$($env:JAVA_HOME)" -ForegroundColor Green
    Write-Host "Si PySpark tiene problemas, considere eliminar y reinstalar."
    Exit
}

if (-Not (Test-Path -Path $InstallDir)) {
    try {
        New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
    } catch {
        Write-Host "Error: No se pudo crear $InstallDir. Intente ejecutar como Administrador." -ForegroundColor Red
        Exit
    }
}

Write-Host "Descargando OpenJDK 11 (Aprox 180MB). Por favor espere..." -ForegroundColor Yellow
Invoke-WebRequest -Uri $DownloadUrl -OutFile $ZipPath

Write-Host "Extrayendo archivos..." -ForegroundColor Yellow
Expand-Archive -Path $ZipPath -DestinationPath $InstallDir -Force

# El zip extrae a una subcarpeta con el número de versión, vamos a renombrarla para estandarizar
$ExtractedSubFolder = Get-ChildItem -Path $InstallDir -Filter "jdk-11*" | Select-Object -First 1
if ($ExtractedSubFolder) {
    if (Test-Path $ExtractDir) { Remove-Item -Recurse -Force $ExtractDir }
    Rename-Item -Path $ExtractedSubFolder.FullName -NewName "jdk-11"
}

Write-Host "Configurando variables de entorno (JAVA_HOME y PATH)..." -ForegroundColor Yellow
$JavaHomePath = $ExtractDir

# Elegir scope basado en privilegios
$Principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$IsAdmin = $Principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
$Scope = if ($IsAdmin) { "Machine" } else { "User" }

[Environment]::SetEnvironmentVariable("JAVA_HOME", $JavaHomePath, $Scope)

$CurrentPath = [Environment]::GetEnvironmentVariable("PATH", $Scope)
$JavaBin = "$JavaHomePath\bin"

if ($CurrentPath -notlike "*$JavaBin*") {
    $NewPath = "$CurrentPath;$JavaBin"
    [Environment]::SetEnvironmentVariable("PATH", $NewPath, $Scope)
    # Actualizar sesión actual también
    $env:PATH = "$env:PATH;$JavaBin"
    $env:JAVA_HOME = $JavaHomePath
}

# Limpiar cache
Remove-Item $ZipPath -ErrorAction SilentlyContinue

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "¡INSTALACIÓN COMPLETADA EXITOSAMENTE!" -ForegroundColor Green
Write-Host "JAVA_HOME configurado en: $JavaHomePath"
Write-Host "NOTA IMPORTANTE: Cierre y vuelva a abrir su terminal o IDE para" -ForegroundColor Magenta
Write-Host "que los cambios en las variables de entorno tengan efecto." -ForegroundColor Magenta
Write-Host "=============================================" -ForegroundColor Cyan
