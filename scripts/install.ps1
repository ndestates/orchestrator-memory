#Requires -Version 5.1
<#
.SYNOPSIS
  Orchestrator template bootstrap installer for Windows (PowerShell).

.DESCRIPTION
  Verifies Git and Python, creates expected directories, syncs per-platform
  manifests, optionally installs the `orchestrator` CLI package (pip), and
  validates required template files.

  For first-time install INTO another app repo, use the CLI after bootstrap:
    orchestrator init C:\path\to\app --no-pr

  Fleet wave deploy to multiple apps is disabled by default. Use per-app
  init/upgrade only (see docs/getting-started/installation.md).

.PARAMETER Cli
  Also run `python -m pip install -e .` so the `orchestrator` command is on PATH.

.PARAMETER Npm
  Install Node wrapper with npm: `npm install -g .` (delegates to Python CLI).

.PARAMETER Pnpm
  Install Node wrapper with pnpm: `pnpm add -g .` (same package; use if you use pnpm).

.PARAMETER Node
  Install Node wrapper: prefer pnpm if on PATH, else npm.

.PARAMETER Ollama
  Install local Ollama via scripts/install-ollama.ps1 (optional BYOM on the host).

.PARAMETER HostTools
  Install host tools (ripgrep/rg) via scripts/install-host-tools.ps1 -Yes.

.PARAMETER SkipWhoAmI
  Skip operator profile scaffold (setup-who-i-am equivalent is bash-only).

.EXAMPLE
  .\scripts\install.ps1

.EXAMPLE
  .\scripts\install.ps1 -Cli

.EXAMPLE
  .\scripts\install.ps1 -Cli -Npm

.EXAMPLE
  .\scripts\install.ps1 -Pnpm

.EXAMPLE
  .\scripts\install.ps1 -Node

.EXAMPLE
  .\scripts\install.ps1 -HostTools

.EXAMPLE
  .\scripts\install.ps1 -Ollama
#>
[CmdletBinding()]
param(
    [switch]$Cli,
    [switch]$Npm,
    [switch]$Pnpm,
    [switch]$Node,
    [switch]$Ollama,
    [switch]$HostTools,
    [switch]$SkipWhoAmI
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

function Write-InstallInfo([string]$Message) {
    Write-Host "[install] $Message"
}

function Require-Command([string]$Name) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "[install] ERROR: required command not found: $Name"
    }
}

Write-InstallInfo "Checking required commands"
Require-Command "git"
Require-Command "python"

if (-not (Test-Path (Join-Path $Root ".git"))) {
    throw "[install] ERROR: run this script from inside the repository (missing .git)."
}

# ripgrep (rg) — CSE + session-security-sweep
$hostToolsScript = Join-Path $Root "scripts\install-host-tools.ps1"
if (Test-Path $hostToolsScript) {
    if ($HostTools) {
        Write-InstallInfo "Ensuring host tools (ripgrep)"
        & $hostToolsScript -Yes
    } elseif (-not (Get-Command rg -ErrorAction SilentlyContinue)) {
        Write-InstallInfo "WARN: rg (ripgrep) missing — CSE session scan skips some controls"
        Write-InstallInfo "      fix: .\scripts\install-host-tools.ps1 -Yes   or  -HostTools on this installer"
        Write-InstallInfo "      WSL: wsl -e bash -lc 'sudo apt-get install -y ripgrep'"
    } else {
        Write-InstallInfo "OK host tools: rg present"
    }
}

Write-InstallInfo "Creating expected directory structure"
@(
    ".github\agents",
    ".github\prompts",
    "docs\codebase",
    "TODO"
) | ForEach-Object {
    $path = Join-Path $Root $_
    if (-not (Test-Path $path)) {
        New-Item -ItemType Directory -Path $path | Out-Null
    }
}

$syncManifests = Join-Path $Root "scripts\sync_manifests.py"
if (Test-Path $syncManifests) {
    Write-InstallInfo "Syncing per-platform manifests"
    & python $syncManifests
    if ($LASTEXITCODE -ne 0) {
        throw "[install] ERROR: sync_manifests.py failed with exit $LASTEXITCODE"
    }
}

Write-InstallInfo "Validating required template files"
$required = @(
    ".github\project-manifest.yaml",
    ".grok\project-manifest.yaml",
    "docs\codebase\README.md",
    "LICENSE"
)
foreach ($rel in $required) {
    $full = Join-Path $Root $rel
    if (-not (Test-Path $full)) {
        throw "[install] ERROR: required file missing: $rel"
    }
    Write-InstallInfo "Found $rel"
}

if ($Cli) {
    Write-InstallInfo "Installing orchestrator CLI package (editable)"
    & python -m pip install -e .
    if ($LASTEXITCODE -ne 0) {
        throw "[install] ERROR: pip install -e . failed with exit $LASTEXITCODE"
    }
    Write-InstallInfo "Verify: orchestrator version"
    & orchestrator version
    if ($LASTEXITCODE -ne 0) {
        Write-InstallInfo "Note: if 'orchestrator' is not found, ensure Python Scripts is on PATH"
        & python -m orchestrator_cli version
    }
}

function Install-NodeWrapper([string]$Manager) {
    Write-InstallInfo "Installing Node package wrapper via $Manager (delegates to Python CLI; host-global)"
    Require-Command $Manager
    if ($Manager -eq "pnpm") {
        & pnpm add -g $Root
        if ($LASTEXITCODE -ne 0) {
            & pnpm add -g "file:$Root"
        }
        if ($LASTEXITCODE -ne 0) {
            throw "[install] ERROR: pnpm add -g failed with exit $LASTEXITCODE"
        }
    } else {
        & npm install -g $Root
        if ($LASTEXITCODE -ne 0) {
            throw "[install] ERROR: npm install -g failed with exit $LASTEXITCODE"
        }
    }
    Write-InstallInfo "Verify: orchestrator version ($Manager global bin must be on PATH)"
    & orchestrator version
    if ($LASTEXITCODE -ne 0) {
        Write-InstallInfo "Note: ensure $Manager global bin directory is on PATH"
    }
}

if ($Node) {
    if (Get-Command pnpm -ErrorAction SilentlyContinue) {
        Install-NodeWrapper "pnpm"
    } elseif (Get-Command npm -ErrorAction SilentlyContinue) {
        Install-NodeWrapper "npm"
    } else {
        throw "[install] ERROR: -Node requires pnpm or npm on PATH"
    }
}

if ($Pnpm) {
    Install-NodeWrapper "pnpm"
}

if ($Npm) {
    Install-NodeWrapper "npm"
}

if (-not $SkipWhoAmI) {
    $who = Join-Path $Root ".grok\memories\who-i-am.md"
    if (-not (Test-Path $who)) {
        Write-InstallInfo "Operator profile missing — create .grok\memories\who-i-am.md (see docs\getting-started\who-i-am-setup.md)"
    }
}

if ($Ollama) {
    Write-InstallInfo "Installing local Ollama (optional BYOM)"
    $ollamaScript = Join-Path $Root "scripts\install-ollama.ps1"
    if (-not (Test-Path $ollamaScript)) {
        throw "[install] ERROR: scripts\install-ollama.ps1 missing"
    }
    & $ollamaScript
    if ($LASTEXITCODE -ne 0) {
        throw "[install] ERROR: install-ollama.ps1 failed with exit $LASTEXITCODE"
    }
}

Write-InstallInfo "Installation checks completed successfully"
Write-InstallInfo "Next: docs\getting-started\installation.md and /chain session-start"
Write-InstallInfo "Per-app install (not fleet wave): orchestrator init C:\path\to\app --no-pr"
Write-InstallInfo "Optional Ollama: .\scripts\install.ps1 -Ollama  (see docs\guides\local-ollama.md)"
Write-InstallInfo "Licensing: docs\reference\licensing.md"
