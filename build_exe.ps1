#!/usr/bin/env powershell
Write-Host "Building MeshPDF executable..." -ForegroundColor Green
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# Install/update dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Clean previous builds
Write-Host "Cleaning previous builds..." -ForegroundColor Yellow
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }

# Build executable
Write-Host "Building executable with PyInstaller..." -ForegroundColor Yellow
pyinstaller MeshPDF.spec

Write-Host ""
if (Test-Path "dist\MeshPDF.exe") {
    Write-Host "✅ Build successful!" -ForegroundColor Green
    Write-Host "Executable created: dist\MeshPDF.exe" -ForegroundColor Green
    Write-Host ""
    Write-Host "You can now run: dist\MeshPDF.exe" -ForegroundColor Cyan
} else {
    Write-Host "❌ Build failed! Check the output above for errors." -ForegroundColor Red
}

Read-Host "Press Enter to continue"