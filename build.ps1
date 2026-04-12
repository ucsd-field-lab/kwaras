# Build script for Kwaras on Windows
# Usage: .\build.ps1

param(
    [string]$Target = "both",
    [switch]$Clean,
    [switch]$OneFile
)

$ErrorActionPreference = "Stop"

function Write-Step($message) {
    Write-Host "[BUILD] $message" -ForegroundColor Cyan
}

function Write-StepDone($message) {
    Write-Host "[BUILD] $message" -ForegroundColor Green
}

function Write-StepError($message) {
    Write-Host "[BUILD] $message" -ForegroundColor Red
}

# Get script directory and project root
$ScriptDir = $PSScriptRoot
if (-not $ScriptDir) {
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}
$ProjectRoot = $ScriptDir

Set-Location $ProjectRoot

# Clean previous builds if requested
if ($Clean) {
    Write-Step "Cleaning previous build artifacts..."
    if (Test-Path "dist") {
        Remove-Item -Path "dist" -Recurse -Force
        Write-StepDone "Removed dist/"
    }
    if (Test-Path "build") {
        Remove-Item -Path "build" -Recurse -Force
        Write-StepDone "Removed build/"
    }
}

# Check and install pyinstaller
Write-Step "Checking pyinstaller..."
try {
    $pyinstallerVersion = pyinstaller --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-StepDone "pyinstaller $pyinstallerVersion is installed"
    }
} catch {
    Write-Step "Installing pyinstaller..."
    pip install "pyinstaller>=5.0,<7.0"
    if ($LASTEXITCODE -ne 0) {
        Write-StepError "Failed to install pyinstaller"
        exit 1
    }
    Write-StepDone "pyinstaller installed"
}

# Determine build options
$onefileArg = ""
if ($OneFile) {
    $onefileArg = "--onefile"
}

# Build GUI executable
if ($Target -eq "gui" -or $Target -eq "both") {
    Write-Step "Building GUI executable..."
    pyinstaller --noconfirm --clean gui.spec $onefileArg
    if ($LASTEXITCODE -eq 0) {
        $guiExe = Get-ChildItem -Path "dist" -Recurse -Filter "gui.exe" -ErrorAction SilentlyContinue
        if ($guiExe) {
            Write-StepDone "GUI executable created: $($guiExe.FullName)"
        } else {
            Write-StepError "GUI executable not found in dist/"
            exit 1
        }
    } else {
        Write-StepError "GUI build failed"
        exit 1
    }
}

# Build CLI executable
if ($Target -eq "cli" -or $Target -eq "both") {
    Write-Step "Building CLI executable..."
    pyinstaller --noconfirm --clean kwaras.spec $onefileArg
    if ($LASTEXITCODE -eq 0) {
        $kwarasExe = Get-ChildItem -Path "dist" -Recurse -Filter "kwaras.exe" -ErrorAction SilentlyContinue
        if ($kwarasExe) {
            Write-StepDone "CLI executable created: $($kwarasExe.FullName)"
        } else {
            Write-StepError "CLI executable not found in dist/"
            exit 1
        }
    } else {
        Write-StepError "CLI build failed"
        exit 1
    }
}

Write-Host ""
Write-Host "Build complete!" -ForegroundColor Green
Write-Host "Executables are in the dist/ directory"