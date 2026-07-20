#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Create the local service account that the File Ingest Service scheduled task
    runs as, and grant it the "Log on as a batch job" right.

.DESCRIPTION
    Creates a dedicated, least-privilege LOCAL account 'svc_fis'. Run once, as
    Administrator, on a STANDALONE (workgroup) server. On a DOMAIN-JOINED server,
    use a domain service account instead and skip this script.
#>

$ErrorActionPreference = "Stop"

$AccountName = "svc_fis"
$FullName    = "File Ingest Service Account"
$Description = "Runs the File Ingest Service scheduled task."

$Password = Read-Host -AsSecureString "Enter a strong password for $AccountName"

if (Get-LocalUser -Name $AccountName -ErrorAction SilentlyContinue) {
    Write-Host "Account '$AccountName' already exists - skipping creation." -ForegroundColor Yellow
} else {
    New-LocalUser -Name $AccountName `
        -Password $Password `
        -FullName $FullName `
        -Description $Description `
        -PasswordNeverExpires `
        -UserMayNotChangePassword
    Write-Host "Created local account '$AccountName'." -ForegroundColor Green
}

# The account needs "Log on as a batch job" (SeBatchLogonRight) or the scheduled
# task fails to launch with 0x41303. Register-ScheduledTask does NOT reliably
# grant this on a standalone server, so we grant it explicitly via secedit.
Write-Host ""
Write-Host "Granting 'Log on as a batch job' to $AccountName ..." -ForegroundColor Cyan

$sid = (Get-LocalUser -Name $AccountName).SID.Value
$tmpDir = [System.IO.Path]::GetTempPath()
$infPath = Join-Path $tmpDir "fis_secpol.inf"
$dbPath  = Join-Path $tmpDir "fis_secpol.sdb"

secedit /export /cfg $infPath /areas USER_RIGHTS | Out-Null
$content = Get-Content $infPath
$line = $content | Where-Object { $_ -match "^SeBatchLogonRight" }

if (-not $line) {
    $content += "SeBatchLogonRight = *$sid"
} elseif ($line -notmatch [regex]::Escape($sid)) {
    $content = $content -replace "^(SeBatchLogonRight\s*=\s*.*)$", "`$1,*$sid"
} else {
    Write-Host "  $AccountName already has the batch-logon right - skipping." -ForegroundColor Yellow
}

if ($line -notmatch [regex]::Escape($sid)) {
    Set-Content -Path $infPath -Value $content -Encoding Unicode
    secedit /configure /db $dbPath /cfg $infPath /areas USER_RIGHTS | Out-Null
    Write-Host "  granted." -ForegroundColor Green
}

Remove-Item $infPath, $dbPath -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "Next: run 02_set_machine_env.ps1 to set machine-scoped configuration." -ForegroundColor Cyan
