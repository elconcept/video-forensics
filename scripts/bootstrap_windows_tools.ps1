[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

function Refresh-ProcessPath {
    $machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $knownPaths = @(
        "$env:ProgramFiles\CMake\bin",
        "$env:ProgramFiles\LLVM\bin",
        "$env:LOCALAPPDATA\Programs\Python\Python312",
        "$env:LOCALAPPDATA\Programs\Python\Python312\Scripts"
    )
    $parts = @($machinePath, $userPath) + $knownPaths
    $env:Path = ($parts | Where-Object { $_ } | Select-Object -Unique) -join ";"
}

function Find-Command {
    param([Parameter(Mandatory)][string[]]$Names)
    foreach ($name in $Names) {
        $command = Get-Command $name -ErrorAction SilentlyContinue
        if ($null -ne $command) {
            return $command.Source
        }
    }
    return $null
}

function Install-WingetPackage {
    param(
        [Parameter(Mandatory)][string]$Id,
        [Parameter(Mandatory)][string]$Label
    )
    $winget = Find-Command -Names @("winget.exe", "winget")
    if (-not $winget) {
        throw "Missing winget; cannot install $Label automatically"
    }
    Write-Host "[bootstrap] Installing $Label ($Id)"
    & $winget install --exact --id $Id --accept-package-agreements --accept-source-agreements --silent
    if ($LASTEXITCODE -ne 0) {
        throw "winget installation failed for $Label ($Id), exit code $LASTEXITCODE"
    }
    Refresh-ProcessPath
}

Refresh-ProcessPath

$python = Find-Command -Names @("python.exe", "python", "py.exe", "py")
if (-not $python) {
    Install-WingetPackage -Id "Python.Python.3.12" -Label "Python 3.12"
    $python = Find-Command -Names @("python.exe", "python", "py.exe", "py")
}

$cmake = Find-Command -Names @("cmake.exe", "cmake")
if (-not $cmake) {
    Install-WingetPackage -Id "Kitware.CMake" -Label "CMake"
    $cmake = Find-Command -Names @("cmake.exe", "cmake")
}

$compiler = Find-Command -Names @("clang++.exe", "clang++", "cl.exe", "cl", "g++.exe", "g++")
if (-not $compiler) {
    Install-WingetPackage -Id "LLVM.LLVM" -Label "LLVM C++ compiler"
    $compiler = Find-Command -Names @("clang++.exe", "clang++", "cl.exe", "cl", "g++.exe", "g++")
}

$missing = @()
if (-not $python) { $missing += "python" }
if (-not $cmake) { $missing += "cmake" }
if (-not $compiler) { $missing += "compiler" }
if ($missing.Count -gt 0) {
    throw "Missing required tools after bootstrap: $($missing -join ', ')"
}

Write-Host "[bootstrap] Python: $python"
Write-Host "[bootstrap] CMake: $cmake"
Write-Host "[bootstrap] Compiler: $compiler"
