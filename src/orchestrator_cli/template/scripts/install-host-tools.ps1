#Requires -Version 5.1
<#
.SYNOPSIS
  Ensure host CLI tools the orchestrator depends on (Windows).

.DESCRIPTION
  Primary tool: ripgrep (rg) for Cyber Essentials scans, session-security-sweep,
  and agent search workflows.

.PARAMETER Check
  Only check; exit 1 if anything missing.

.PARAMETER Yes
  Non-interactive install via winget (preferred) or chocolatey.

.PARAMETER DryRun
  Print planned actions only.

.EXAMPLE
  .\scripts\install-host-tools.ps1

.EXAMPLE
  .\scripts\install-host-tools.ps1 -Yes
#>
[CmdletBinding()]
param(
    [switch]$Check,
    [switch]$Yes,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Write-Info([string]$Message) {
    Write-Host "[host-tools] $Message"
}

function Test-Rg {
    return [bool](Get-Command rg -ErrorAction SilentlyContinue)
}

function Get-RgVersion {
    if (Test-Rg) {
        try {
            return ((& rg --version 2>$null | Select-Object -First 1) -join " ")
        } catch {
            return "present"
        }
    }
    return "MISSING"
}

Write-Info "Checking ripgrep (rg)"
if (Test-Rg) {
    Write-Info "OK rg: $(Get-RgVersion)"
    exit 0
}

Write-Info "MISSING rg (ripgrep)"
if ($Check) {
    Write-Host @"
[host-tools] Install ripgrep on Windows:
  winget install BurntSushi.ripgrep.MSVC
  # or: choco install ripgrep
  # or: scoop install ripgrep
  # WSL2 (recommended for orchestrator Linux scripts):
  #   wsl -e bash -lc 'sudo apt-get update && sudo apt-get install -y ripgrep'
  #   or from repo in WSL: bash scripts/install-host-tools.sh --yes
"@
    exit 1
}

if (-not $Yes -and -not $DryRun) {
    $ans = Read-Host "[host-tools] Install ripgrep via winget/choco? [y/N]"
    if ($ans -notmatch '^[yY]') {
        Write-Info "skipped install"
        exit 1
    }
}

if ($DryRun) {
    Write-Info "dry-run: winget install BurntSushi.ripgrep.MSVC (or choco install ripgrep)"
    exit 0
}

if (Get-Command winget -ErrorAction SilentlyContinue) {
    Write-Info "installing via winget"
    winget install --id BurntSushi.ripgrep.MSVC -e --accept-source-agreements --accept-package-agreements
} elseif (Get-Command choco -ErrorAction SilentlyContinue) {
    Write-Info "installing via chocolatey"
    choco install ripgrep -y
} elseif (Get-Command scoop -ErrorAction SilentlyContinue) {
    Write-Info "installing via scoop"
    scoop install ripgrep
} else {
    Write-Error "[host-tools] No winget/choco/scoop found. Install manually: https://github.com/BurntSushi/ripgrep#installation"
    exit 1
}

# Refresh PATH for current session if possible
$machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($machinePath -or $userPath) {
    $env:Path = @($machinePath, $userPath, $env:Path) -join ";"
}

if (Test-Rg) {
    Write-Info "OK rg: $(Get-RgVersion)"
    exit 0
}

Write-Info "Installed but rg not on PATH yet — open a new terminal, or use WSL: bash scripts/install-host-tools.sh --yes"
exit 1
