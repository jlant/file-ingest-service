#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Set machine-scoped configuration for the File Ingest Service.

.DESCRIPTION
    The scheduled task runs non-interactively as svc_fis, so any configuration
    supplied by environment variable must be set at MACHINE scope, not tied to an
    interactive user profile.

    This service currently has NO SECRETS - it reads and writes local directories
    only. What it does have is a machine-specific path: the data directory. That
    belongs here rather than in the committed config\app.toml, because it differs
    per server.

    If you later add a setting that IS a secret (a database password, an API
    key), add it here with Set-MachineSecret below - never in app.toml, which is
    committed to source control.

    After running this, a NEW process must start to see the variables. The
    scheduled task picks them up on its next run automatically.
#>

param(
    [string]$DataDir = "C:\FileIngest\data"
)

$ErrorActionPreference = "Stop"

function Set-MachineSecret {
    <#
        Prompt for a secret and store it at machine scope without echoing it.
        Unused today - kept as the pattern to follow when this service gains a
        credential. Example: Set-MachineSecret -Name "APP_DB_PASSWORD"
    #>
    param([string]$Name)
    $secure = Read-Host -AsSecureString "Enter value for $Name"
    $bstr   = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try {
        $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
        [Environment]::SetEnvironmentVariable($Name, $plain, "Machine")
        Write-Host "Set $Name (Machine scope)." -ForegroundColor Green
    } finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
}

Write-Host "=== Set machine-scoped configuration ===" -ForegroundColor Cyan

[Environment]::SetEnvironmentVariable("APP_DATA_DIR", $DataDir, "Machine")
Write-Host "  APP_DATA_DIR = $DataDir" -ForegroundColor Green

Write-Host ""
Write-Host "=== Create the data directories and grant svc_fis access ===" -ForegroundColor Cyan
foreach ($sub in @("inbox", "processed", "error")) {
    $dir = Join-Path $DataDir $sub
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    Write-Host "  $dir"
}
icacls $DataDir /grant "svc_fis:(OI)(CI)M" /T | Out-Null
Write-Host "  granted svc_fis modify on $DataDir" -ForegroundColor Green

Write-Host ""
Write-Host "Verify (in a NEW elevated shell) with:" -ForegroundColor Cyan
Write-Host '  [Environment]::GetEnvironmentVariable("APP_DATA_DIR","Machine")' -ForegroundColor DarkGray
Write-Host ""
Write-Host "Next: deploy the code, then run 03_register_task.ps1." -ForegroundColor Cyan
