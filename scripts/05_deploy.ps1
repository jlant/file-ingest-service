#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Deploy or update the File Ingest Service: pull the latest code, build the
    locked virtual environment, run the test gate, then hand off to the task.

.DESCRIPTION
    Works for both first install (after git clone) and ongoing updates. Every
    step is built on the committed uv.lock, so the dependency set is identical
    and reproducible. Safe to re-run.

      1. git pull            - latest code AND lockfile (skipped with -NoPull)
      2. uv sync --frozen    - build .venv to match the lockfile EXACTLY
      3. uv run pytest       - gate: a failed deploy leaves the prior code running
      4. ensure log dir + permissions for svc_fis
#>

param(
    [string]$InstallDir     = "C:\Apps\file-ingest-service",
    [string]$UvPath         = "C:\ProgramData\uv\bin\uv.exe",
    [string]$ServiceAccount = "svc_fis",
    [switch]$NoPull,
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path (Join-Path $InstallDir "pyproject.toml"))) {
    throw "No pyproject.toml in $InstallDir - is the repo cloned there?"
}

Set-Location $InstallDir

Write-Host "=== 1. Get latest code ===" -ForegroundColor Cyan
if ($NoPull) {
    Write-Host "  -NoPull set; using code already on disk." -ForegroundColor Yellow
} else {
    git pull
}
$commit = (git rev-parse --short HEAD).Trim()
Write-Host "  at commit $commit" -ForegroundColor Green

Write-Host ""
Write-Host "=== 2. Build the locked virtual environment ===" -ForegroundColor Cyan
& $UvPath sync --frozen
Write-Host "  .venv synced to uv.lock" -ForegroundColor Green

if (-not $SkipTests) {
    Write-Host ""
    Write-Host "=== 3. Run the test gate ===" -ForegroundColor Cyan
    & $UvPath run pytest -q
    if ($LASTEXITCODE -ne 0) {
        throw "Tests failed - deploy aborted. The scheduled task keeps running the prior code."
    }
    Write-Host "  tests passed" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "=== 3. Tests SKIPPED (-SkipTests) ===" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== 4. Ensure log directory exists and is writable by $ServiceAccount ===" -ForegroundColor Cyan
$logDir = Join-Path $InstallDir "logs"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
icacls $logDir /grant "${ServiceAccount}:(OI)(CI)M" /T | Out-Null
Write-Host "  $logDir writable by $ServiceAccount" -ForegroundColor Green

Write-Host ""
Write-Host "Deploy complete at commit $commit." -ForegroundColor Green
Write-Host ""
Write-Host "First-time setup still needed (run once, in order):" -ForegroundColor Cyan
Write-Host "  01_create_service_account.ps1   (create svc_fis)" -ForegroundColor DarkGray
Write-Host "  02_set_machine_env.ps1          (set APP_DATA_DIR, create data dirs)" -ForegroundColor DarkGray
Write-Host "  03_register_task.ps1            (register the every-minute task)" -ForegroundColor DarkGray
Write-Host "  04_smoke_test.ps1               (verify it actually runs)" -ForegroundColor DarkGray
Write-Host ""
Write-Host "For an UPDATE (account/task already exist), this script + 04 is all you need." -ForegroundColor Cyan
