#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Register the File Ingest Service scheduled task: run once per minute, every
    day, whether or not a user is logged on, with no overlapping runs.

.DESCRIPTION
    Encodes the three production-safety properties for a once-a-minute job:
      1. No overlap  - if a run exceeds 60s, the next trigger is skipped.
      2. Run whether-logged-on-or-not - survives reboots and logoffs.
      3. Least-privilege identity - runs as svc_fis, not SYSTEM/admin.

    Invokes `uv run fis run` in the install directory, using the project's
    locked virtual environment.
#>

param(
    [string]$InstallDir = "C:\Apps\file-ingest-service",
    [string]$UvPath     = "C:\ProgramData\uv\bin\uv.exe",
    [string]$Account    = ".\svc_fis",
    [string]$TaskName   = "FileIngestService"
)

$ErrorActionPreference = "Stop"

# --- Normalize the account name for reliable SID resolution ---
# Task Scheduler resolves "COMPUTERNAME\user" more reliably than ".\user"
# (which can fail with 0x80070534). Convert ".\user" or a bare "user" into
# "$env:COMPUTERNAME\user"; leave an already-qualified name as-is.
if ($Account -like ".\*") {
    $Account = "$env:COMPUTERNAME\" + $Account.Substring(2)
} elseif ($Account -notlike "*\*") {
    $Account = "$env:COMPUTERNAME\$Account"
}
Write-Host "Registering task to run as: $Account" -ForegroundColor Cyan

# This script uses splatting (a parameter hashtable passed with @) rather than
# backtick line-continuation: a comment after a backtick silently breaks the
# continuation, so splatting is both safer and more readable.

# --- Action: run one pass of the ingest in the install directory ---
$actionArgs = @{
    Execute          = $UvPath
    Argument         = "run fis run --config `"$InstallDir\config\app.toml`""
    WorkingDirectory = $InstallDir
}
$action = New-ScheduledTaskAction @actionArgs

# --- Trigger: every 1 minute, indefinitely, starting now ---
# For an INDEFINITE repetition you OMIT the duration entirely - do NOT pass
# [TimeSpan]::MaxValue, which the Task Scheduler engine rejects as out of range.
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date)
$repeatSource = New-ScheduledTaskTrigger -Once -At (Get-Date) `
    -RepetitionInterval (New-TimeSpan -Minutes 1)
$trigger.Repetition = $repeatSource.Repetition

# --- Settings: the production-safety knobs ---
$settingsArgs = @{
    MultipleInstances  = "IgnoreNew"                    # NO OVERLAP
    StartWhenAvailable = $true                          # catch up after downtime
    DontStopOnIdleEnd  = $true
    ExecutionTimeLimit = (New-TimeSpan -Minutes 5)      # kill a hung run
    RestartCount       = 0
}
$settings = New-ScheduledTaskSettingsSet @settingsArgs

# --- Principal: least privilege, run whether logged on or not ---
$principalArgs = @{
    UserId    = $Account
    LogonType = "Password"
    RunLevel  = "Limited"
}
$principal = New-ScheduledTaskPrincipal @principalArgs

$task = New-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -Principal $principal

# --- Register. Prompt for the password IN THE TERMINAL (not the GUI dialog, ---
# which has focus-handling quirks). Read as SecureString, convert only at use,
# and zero the memory afterward.
$securePw = Read-Host -AsSecureString "Enter the password for $Account"
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePw)
try {
    $plainPw = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)

    $registerArgs = @{
        TaskName    = $TaskName
        InputObject = $task
        User        = $Account
        Password    = $plainPw
        Force       = $true
    }
    Register-ScheduledTask @registerArgs
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
}

Write-Host ""
Write-Host "Registered scheduled task '$TaskName'." -ForegroundColor Green
Write-Host "It will run 'uv run fis run' every minute as $Account." -ForegroundColor Green
Write-Host ""
Write-Host "Verify with:" -ForegroundColor Cyan
Write-Host "  Get-ScheduledTask -TaskName $TaskName | Get-ScheduledTaskInfo" -ForegroundColor DarkGray
