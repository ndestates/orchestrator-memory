#Requires -Version 5.1
<#
.SYNOPSIS
  Install Ollama on Windows via winget or the official installer.

.DESCRIPTION
  Detects local Ollama CLI + API, then installs when missing using winget
  (preferred) or the official OllamaSetup.exe download.

.PARAMETER CheckOnly
  Detect only; do not install.

.EXAMPLE
  .\scripts\install-ollama.ps1

.EXAMPLE
  .\scripts\install-ollama.ps1 -CheckOnly
#>
[CmdletBinding()]
param(
    [switch]$CheckOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RootDir = Split-Path -Parent $PSScriptRoot
Set-Location $RootDir

function Write-Info([string]$Message) {
    Write-Host "[install-ollama] $Message"
}

function Find-Python() {
    foreach ($candidate in @('py', 'python', 'python3')) {
        try {
            $null = & $candidate --version 2>&1
            if ($LASTEXITCODE -eq 0) { return $candidate }
        } catch {
            continue
        }
    }
    return $null
}

$py = Find-Python
if ($null -eq $py) {
    throw 'Python 3 is required for detection — install from https://www.python.org/downloads/'
}

$reportJson = & $py scripts/ollama_detect.py --root $RootDir --json
$report = $reportJson | ConvertFrom-Json

if ($report.ollama_binary -eq 'yes') {
    Write-Info 'Ollama CLI already installed'
    if ($report.ollama_api -eq 'reachable') {
        Write-Info 'Ollama API reachable'
    } else {
        Write-Info 'Ollama API not reachable — start the Ollama app from the Start menu'
    }
    exit 0
}

if ($CheckOnly) {
    Write-Info 'Ollama not installed (check-only)'
    exit 1
}

Write-Info 'Installing Ollama on Windows'

if (Get-Command winget -ErrorAction SilentlyContinue) {
    Write-Info 'Trying winget install Ollama.Ollama'
    winget install --id Ollama.Ollama -e --accept-source-agreements --accept-package-agreements
    if ($LASTEXITCODE -eq 0) {
        Write-Info 'Ollama installed via winget — restart the terminal if ollama is not on PATH'
        exit 0
    }
    Write-Info 'winget install failed — falling back to official installer download'
}

$installer = Join-Path $env:TEMP 'OllamaSetup.exe'
Write-Info "Downloading official installer to $installer"
Invoke-WebRequest -Uri 'https://ollama.com/download/OllamaSetup.exe' -OutFile $installer
Write-Info 'Running OllamaSetup.exe (silent)'
Start-Process -FilePath $installer -ArgumentList '/S' -Wait

$reportJson = & $py scripts/ollama_detect.py --root $RootDir --json
$report = $reportJson | ConvertFrom-Json
if ($report.ollama_binary -ne 'yes') {
    throw 'Install finished but ollama CLI still not on PATH — restart PowerShell and run: ollama --version'
}

Write-Info 'Ollama installed — verify with: ollama --version'
Write-Info 'Pull a model: ollama pull llama3.2'
Write-Info 'Docs: docs/guides/local-ollama.md'