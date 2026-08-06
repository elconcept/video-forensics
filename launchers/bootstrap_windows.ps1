$ErrorActionPreference = "Stop"

function Write-Bootstrap([string]$Message) {
    Write-Host "[bootstrap] $Message"
}

function Test-Command([string]$Name) {
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Install-WingetPackage([string]$Id, [bool]$Required) {
    if (-not (Test-Command "winget")) { return $false }
    Write-Bootstrap "Instalowanie przez winget: $Id"
    & winget install --exact --id $Id --accept-package-agreements --accept-source-agreements --silent
    if ($LASTEXITCODE -eq 0) { return $true }
    if ($Required) { throw "Nie udało się zainstalować wymaganego pakietu: $Id" }
    Write-Bootstrap "Opcjonalny pakiet winget niedostępny: $Id"
    return $false
}

function Install-ChocoPackage([string]$Name, [bool]$Required) {
    if (-not (Test-Command "choco")) { return $false }
    Write-Bootstrap "Instalowanie przez Chocolatey: $Name"
    & choco install $Name -y --no-progress
    if ($LASTEXITCODE -eq 0) { return $true }
    if ($Required) { throw "Nie udało się zainstalować wymaganego pakietu: $Name" }
    Write-Bootstrap "Opcjonalny pakiet Chocolatey niedostępny: $Name"
    return $false
}

function Install-PackageFallback(
    [string]$Command,
    [string]$WingetId,
    [string]$ChocoName,
    [bool]$Required
) {
    if (Test-Command $Command) { return }
    $installed = Install-WingetPackage $WingetId $false
    if (-not $installed) {
        $installed = Install-ChocoPackage $ChocoName $false
    }
    if ($Required -and -not $installed) {
        throw "Brak wymaganego narzędzia: $Command"
    }
}

$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCommand) {
    $pythonCommand = Get-Command py -ErrorAction SilentlyContinue
}

if (-not $pythonCommand) {
    Write-Bootstrap "Nie wykryto Pythona. Rozpoczynam instalację Python 3.12."

    if (-not (Test-Command "winget") -and -not (Test-Command "choco")) {
        throw "Brak Pythona oraz menedżera pakietów winget lub Chocolatey."
    }

    $installed = Install-WingetPackage "Python.Python.3.12" $false
    if (-not $installed) {
        $installed = Install-ChocoPackage "python312" $false
    }
    if (-not $installed) {
        throw "Nie udało się zainstalować Python 3.12."
    }

    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
        [Environment]::GetEnvironmentVariable("Path", "User")

    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCommand) {
        $pythonCommand = Get-Command py -ErrorAction SilentlyContinue
    }
    if (-not $pythonCommand) {
        throw "Python został zainstalowany, ale nie jest dostępny w PATH. Uruchom ponownie PowerShell."
    }
}

if (-not (Test-Command "winget") -and -not (Test-Command "choco")) {
    throw "Brak winget i Chocolatey. Zainstaluj App Installer albo Chocolatey."
}
Install-PackageFallback "ffmpeg" "Gyan.FFmpeg" "ffmpeg" $true
Install-PackageFallback "mediainfo" "MediaArea.MediaInfo.GUI" "mediainfo" $false
Install-PackageFallback "exiftool" "OliverBetz.ExifTool" "exiftool" $false
Install-PackageFallback "tesseract" "UB-Mannheim.TesseractOCR" "tesseract" $false
Install-PackageFallback "MP4Box" "GPAC.GPAC" "gpac" $false

$env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
    [Environment]::GetEnvironmentVariable("Path", "User")

if (-not (Test-Command "python")) { throw "Brak python po bootstrapie" }
if (-not (Test-Command "ffmpeg")) { throw "Brak ffmpeg po bootstrapie" }
if (-not (Test-Command "ffprobe")) { throw "Brak ffprobe po bootstrapie" }

$pythonExe = $pythonCommand.Source
$pythonArgs = @()
if ($pythonCommand.Name -eq "py.exe" -or $pythonCommand.Name -eq "py") {
    $pythonArgs = @("-3.12")
}

if (-not (Test-Path -LiteralPath ".venv")) {
    Write-Bootstrap "Tworzenie .venv"
    & $pythonExe @pythonArgs -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        throw "Nie udało się utworzyć środowiska .venv."
    }
}

& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -e ".[dev]"

Write-Bootstrap "Bootstrap Windows zakończony"
