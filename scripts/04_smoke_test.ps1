#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Verify the File Ingest Service is correctly installed and the scheduled task
    actually runs. Catches the "registered but silently broken" failure.
#>

param(
    [string]$InstallDir = "C:\Apps\file-ingest-service",
    [string]$UvPath     = "C:\ProgramData\uv\bin\uv.exe",
    [string]$TaskName   = "FileIngestService"
)

$ErrorActionPreference = "Stop"

Write-Host "=== 1. uv is reachable at the path the task uses ===" -ForegroundColor Cyan
if (Test-Path $UvPath) {
    & $UvPath --version
    Write-Host "OK: uv found at $UvPath" -ForegroundColor Green
} else {
    Write-Host "FAIL: uv not at $UvPath. A per-user uv install is NOT visible to" -ForegroundColor Red
    Write-Host "      svc_fis. Install uv machine-wide (00_install_uv_machine_wide.ps1)." -ForegroundColor Red
}

Write-Host ""
Write-Host "=== 2. Config resolves (no files processed) ===" -ForegroundColor Cyan
Push-Location $InstallDir
try {
    & $UvPath run fis read-config --config "$InstallDir\config\app.toml"
} finally {
    Pop-Location
}
Write-Host "Check above: data_dir should be the real machine path, env=PROD." -ForegroundColor Yellow

Write-Host ""
Write-Host "=== 3. Seed a sample file into the inbox ===" -ForegroundColor Cyan
Push-Location $InstallDir
try {
    & $UvPath run fis seed --filename "smoke_test.txt" --content "smoke test" `
        --config "$InstallDir\config\app.toml"
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "=== 4. Force one immediate task run, then inspect result ===" -ForegroundColor Cyan
Start-ScheduledTask -TaskName $TaskName

$deadline = (Get-Date).AddSeconds(45)
do {
    Start-Sleep -Seconds 3
    $task = Get-ScheduledTask -TaskName $TaskName
    $info = $task | Get-ScheduledTaskInfo
    $state = $task.State
    Write-Host "  state=$state last_run=$($info.LastRunTime)" -ForegroundColor DarkGray
} while ($state -eq "Running" -and (Get-Date) -lt $deadline)

$resultHex = "0x{0:X}" -f $info.LastTaskResult
Write-Host "LastRunTime    : $($info.LastRunTime)"
Write-Host "LastTaskResult : $resultHex   (0x0 = success)"
if ($info.LastTaskResult -eq 0) {
    Write-Host "OK: task ran and exited 0." -ForegroundColor Green
} else {
    Write-Host "Task exited non-zero. Common codes:" -ForegroundColor Yellow
    Write-Host "  0x1     - app raised (check the app log below)" -ForegroundColor DarkGray
    Write-Host "  0x41301 - still running (the poll above timed out)" -ForegroundColor DarkGray
    Write-Host "  0x2     - file not found (uv path or install dir wrong)" -ForegroundColor DarkGray
    Write-Host "  0x41303 - task has never run (batch-logon right / registration)" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "=== 5. Confirm the seeded file was processed ===" -ForegroundColor Cyan
$dataDir = [Environment]::GetEnvironmentVariable("APP_DATA_DIR", "Machine")
if ($dataDir) {
    $processed = Join-Path $dataDir "processed\smoke_test.txt"
    $errored   = Join-Path $dataDir "error\smoke_test.txt"
    if (Test-Path $processed) {
        Write-Host "OK: file routed to processed - $processed" -ForegroundColor Green
    } elseif (Test-Path $errored) {
        Write-Host "File was QUARANTINED to error - $errored" -ForegroundColor Yellow
        Write-Host "  (check the log for the validation failure reason)" -ForegroundColor DarkGray
    } else {
        Write-Host "File not found in processed or error - did the run happen?" -ForegroundColor Yellow
    }
} else {
    Write-Host "APP_DATA_DIR not set at machine scope - run 02_set_machine_env.ps1." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== 6. Tail the application log ===" -ForegroundColor Cyan
$log = Join-Path $InstallDir "logs\file_ingest_service.log"
if (Test-Path $log) {
    Get-Content $log -Tail 15
} else {
    Write-Host "No log at $log yet. If the task ran as svc_fis, confirm that" -ForegroundColor Yellow
    Write-Host "account can WRITE to the logs directory." -ForegroundColor Yellow
}
