#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Install uv machine-wide under C:\ProgramData\uv so every account - including
    the non-interactive svc_fis service account - shares one binary, one set of
    managed Pythons, and one package cache.

.DESCRIPTION
    A per-user uv install is invisible to the scheduled-task service account.
    This relocates uv to a shared, machine-readable root and sets machine-scoped
    environment variables so uv keeps ALL of its state there, not in any user
    profile. Run once, elevated. Safe to re-run.
#>

param(
    [string]$Root          = "C:\ProgramData\uv",
    [string]$UvDownloadUrl = "https://astral.sh/uv/install.ps1"
)

$ErrorActionPreference = "Stop"

$BinDir    = Join-Path $Root "bin"
$PythonDir = Join-Path $Root "python"
$CacheDir  = Join-Path $Root "cache"

Write-Host "=== 1. Create the shared uv directory tree ===" -ForegroundColor Cyan
foreach ($d in @($Root, $BinDir, $PythonDir, $CacheDir)) {
    if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
    Write-Host "  $d"
}

Write-Host ""
Write-Host "=== 2. Set machine-scoped uv environment variables ===" -ForegroundColor Cyan
[Environment]::SetEnvironmentVariable("UV_INSTALL_DIR",        $BinDir,    "Machine")
[Environment]::SetEnvironmentVariable("UV_PYTHON_INSTALL_DIR", $PythonDir, "Machine")
[Environment]::SetEnvironmentVariable("UV_CACHE_DIR",          $CacheDir,  "Machine")
[Environment]::SetEnvironmentVariable("UV_PYTHON_PREFERENCE",  "only-managed", "Machine")
Write-Host "  UV_INSTALL_DIR        = $BinDir"
Write-Host "  UV_PYTHON_INSTALL_DIR = $PythonDir"
Write-Host "  UV_CACHE_DIR          = $CacheDir"
Write-Host "  UV_PYTHON_PREFERENCE  = only-managed"

Write-Host ""
Write-Host "=== 3. Add the uv bin dir to the MACHINE PATH (once) ===" -ForegroundColor Cyan
$machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
if ($machinePath -notlike "*$BinDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$machinePath;$BinDir", "Machine")
    Write-Host "  Added $BinDir to machine PATH."
} else {
    Write-Host "  $BinDir already on machine PATH - skipping."
}

Write-Host ""
Write-Host "=== 4. Install uv into the shared bin dir ===" -ForegroundColor Cyan
$env:UV_INSTALL_DIR = $BinDir
Invoke-RestMethod -Uri $UvDownloadUrl | Invoke-Expression

Write-Host ""
Write-Host "=== 5. Lock down permissions (least privilege) ===" -ForegroundColor Cyan
foreach ($writable in @($PythonDir, $CacheDir)) {
    icacls $writable /grant "Users:(OI)(CI)M" /T | Out-Null
    Write-Host "  granted Users modify on $writable"
}
icacls $BinDir /grant "Users:(OI)(CI)RX" /T | Out-Null
Write-Host "  granted Users read/execute on $BinDir"

Write-Host ""
Write-Host "Done. OPEN A NEW ELEVATED SHELL, then verify:" -ForegroundColor Green
Write-Host '  & "C:\ProgramData\uv\bin\uv.exe" --version' -ForegroundColor DarkGray
