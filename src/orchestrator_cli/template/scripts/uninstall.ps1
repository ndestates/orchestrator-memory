#Requires -Version 5.1
<#
.SYNOPSIS
  Uninstall orchestrator host CLI packages and/or remove template surfaces from a project.

.PARAMETER HostPackages
  Uninstall global npm (@ndestates/orchestrator) and pip (orchestrator).

.PARAMETER Project
  Path to app project to strip of orchestrator template files.

.PARAMETER Apply
  Actually perform uninstall (default is dry-run).

.PARAMETER Yes
  Required with -Apply to delete project files.

.EXAMPLE
  .\scripts\uninstall.ps1 -HostPackages

.EXAMPLE
  .\scripts\uninstall.ps1 -Project C:\apps\my-app -Apply -Yes
#>
param(
  [switch]$HostPackages,
  [string]$Project = "",
  [switch]$Apply,
  [switch]$Yes,
  [switch]$NoProject
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
if (-not $Root) { $Root = (Get-Location).Path }
$env:PYTHONPATH = "$Root\src;$Root\scripts;$($env:PYTHONPATH)"

$argsList = @("uninstall")
if ($HostPackages) { $argsList += "--host" }
if ($NoProject -or ($HostPackages -and -not $Project)) {
  $argsList += "--no-project"
}
if ($Project) {
  $argsList += $Project
} elseif (-not $HostPackages) {
  $argsList += "."
}
if ($Apply) { $argsList += "--apply" }
if ($Yes) { $argsList += "--yes" }

$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { $py = Get-Command py -ErrorAction SilentlyContinue }
if (-not $py) {
  Write-Error "Python not found on PATH"
  exit 1
}

if ($py.Name -eq "py.exe" -or $py.Name -eq "py") {
  & py -3 -m orchestrator_cli @argsList
} else {
  & python -m orchestrator_cli @argsList
}
exit $LASTEXITCODE
