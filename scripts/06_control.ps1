#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Control the File Ingest Service scheduled task: check status, pause
    (disable), resume (enable), stop an in-flight run, or trigger a run now.

.DESCRIPTION
    A single documented entry point for the common operational actions. The
    default action (no switch) is -Status, which only reads state.

    Pausing is lossless: while the task is disabled, files simply accumulate in
    the inbox directory and are processed when it is re-enabled.
#>

param(
    [string]$TaskName = "FileIngestService",
    [switch]$Status,
    [switch]$Disable,
    [switch]$Enable,
    [switch]$StopRunning,
    [switch]$RunNow
)

$ErrorActionPreference = "Stop"

if ($Disable -and $Enable) {
    throw "Specify only one of -Disable or -Enable, not both."
}

$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if (-not $task) {
    throw "Scheduled task '$TaskName' not found. Has it been registered (03_register_task.ps1)?"
}

function Show-Status {
    $t = Get-ScheduledTask -TaskName $TaskName
    $info = $t | Get-ScheduledTaskInfo
    $resultHex = "0x{0:X}" -f $info.LastTaskResult
    Write-Host ""
    Write-Host "Task           : $TaskName" -ForegroundColor Cyan
    Write-Host "State          : $($t.State)"
    Write-Host "Last run time  : $($info.LastRunTime)"
    Write-Host "Last result    : $resultHex   (0x0 = success)"
    Write-Host "Next run time  : $($info.NextRunTime)"
    Write-Host ""
}

if ($StopRunning) {
    Write-Host "Stopping any in-flight run of '$TaskName' ..." -ForegroundColor Yellow
    Stop-ScheduledTask -TaskName $TaskName
    Write-Host "  done." -ForegroundColor Green
}

if ($Disable) {
    Disable-ScheduledTask -TaskName $TaskName | Out-Null
    Write-Host "Task '$TaskName' DISABLED - it will not fire until re-enabled." -ForegroundColor Yellow
    Write-Host "Files will accumulate in the inbox and process when you re-enable." -ForegroundColor DarkGray
}

if ($Enable) {
    Enable-ScheduledTask -TaskName $TaskName | Out-Null
    Write-Host "Task '$TaskName' ENABLED - it will fire on schedule again." -ForegroundColor Green
}

if ($RunNow) {
    Write-Host "Triggering one run of '$TaskName' now ..." -ForegroundColor Cyan
    Start-ScheduledTask -TaskName $TaskName
    Write-Host "  triggered (check status or the log for the result)." -ForegroundColor Green
}

Show-Status
