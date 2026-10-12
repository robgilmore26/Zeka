# Voice the course with Azure Speech, then build the review page.
#
#   powershell -ExecutionPolicy Bypass -File tools\audio\run-azure.ps1            # A1 first
#   powershell -ExecutionPolicy Bypass -File tools\audio\run-azure.ps1 -Levels all
#
# Asks for the Azure Speech key (typed input is hidden, and it is not saved in
# shell history) and the region, unless AZURE_SPEECH_KEY / AZURE_SPEECH_REGION
# are already set. The key lives only in this terminal session.
param([string]$Levels = 'A1')

Set-Location (Join-Path $PSScriptRoot '..\..')

if (-not $env:AZURE_SPEECH_KEY) {
    $secure = Read-Host 'Paste your Azure Speech key (input is hidden)' -AsSecureString
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try { $env:AZURE_SPEECH_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
}
if (-not $env:AZURE_SPEECH_REGION) {
    $env:AZURE_SPEECH_REGION = (Read-Host 'Region (the short name under Keys and Endpoint, e.g. westeurope)').Trim().ToLower()
}

$env:PYTHONIOENCODING = 'utf-8'
$cmd = @('tools\audio\build.py', 'generate', '--engine', 'azure', '--verify')
if ($Levels -ne 'all') { $cmd += @('--levels', $Levels) }
py @cmd
if ($LASTEXITCODE -eq 0) {
    Write-Host ''
    Write-Host 'Done. Tell Claude, and it will open the review page for you.' -ForegroundColor Green
}
