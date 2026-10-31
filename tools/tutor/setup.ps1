# One-time setup (and later updates) for Zeka Speaking Practice.
#
#   powershell -ExecutionPolicy Bypass -File tools\tutor\setup.ps1
#
# 1. Installs the server's packages and logs you in to Cloudflare (a browser opens).
# 2. Asks for your ElevenLabs and Anthropic API keys (typed input is hidden; the
#    keys go straight to Cloudflare as secrets and are not saved on this PC).
# 3. Finds the "Ivan - Deep Serbian & Croatian (Balkan)" voice and adds it to your
#    ElevenLabs voices, asks which email may use the tutor, and deploys.
# At the end it prints the server address: send that to Claude.
#
# To redeploy code changes only, without touching the keys: -DeployOnly
# To use a different voice: -VoiceId <id>
param([switch]$DeployOnly, [string]$VoiceId = '')

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

function Read-Secret([string]$prompt) {
    $secure = Read-Host $prompt -AsSecureString
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try { return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
}
function Put-Secret([string]$name, [string]$value) {
    $value | npx wrangler secret put $name | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Could not save $name" }
    Write-Host "  saved $name" -ForegroundColor DarkGray
}

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host 'Node.js is needed. Install the LTS version from https://nodejs.org, then run this again.' -ForegroundColor Yellow
    exit 1
}

Write-Host 'Installing packages...'
npm install --no-fund --no-audit
if ($LASTEXITCODE -ne 0) { throw 'npm install failed' }
npm test
if ($LASTEXITCODE -ne 0) { throw 'The server tests failed; tell Claude' }

Write-Host 'Logging in to Cloudflare (a browser window opens; create a free account if you do not have one)...'
npx wrangler whoami *> $null
if ($LASTEXITCODE -ne 0) { npx wrangler login }

if (-not $DeployOnly) {
    # The Worker must exist before secrets can be added to it
    npx wrangler deploy | Out-Null

    $eleven = Read-Secret 'Paste your ElevenLabs API key (input is hidden)'
    if (-not $VoiceId) {
        Write-Host 'Looking up the Ivan voice in the ElevenLabs voice library...'
        $h = @{ 'xi-api-key' = $eleven }
        $res = Invoke-RestMethod -Headers $h -Uri 'https://api.elevenlabs.io/v1/shared-voices?search=Ivan&page_size=30'
        $found = @($res.voices | Where-Object { $_.name -match 'Ivan' -and $_.name -match 'Serbian' })
        if ($found.Count -eq 0) {
            Write-Host 'Could not find it automatically. Open the Voice Library on elevenlabs.io, add "Ivan - Deep Serbian & Croatian (Balkan)" to My Voices, copy its Voice ID and run:' -ForegroundColor Yellow
            Write-Host '  powershell -ExecutionPolicy Bypass -File tools\tutor\setup.ps1 -VoiceId <the id>'
            exit 1
        }
        $v = $found[0]
        Write-Host ("Found: " + $v.name + "  (" + $v.voice_id + ")")
        try {
            $added = Invoke-RestMethod -Method Post -Headers $h -ContentType 'application/json' `
                -Uri ("https://api.elevenlabs.io/v1/voices/add/" + $v.public_owner_id + "/" + $v.voice_id) `
                -Body (@{ new_name = 'Ivan (Zeka tutor)' } | ConvertTo-Json)
            $VoiceId = $added.voice_id
            Write-Host "Added it to your ElevenLabs voices."
        } catch {
            Write-Host 'It may already be in your voices; using its library id.' -ForegroundColor DarkGray
            $VoiceId = $v.voice_id
        }
    }
    $anthropic = Read-Secret 'Paste your Anthropic API key (input is hidden)'
    $emails = (Read-Host 'Email address you sign in to Zeka with (several: separate with commas)').Trim()

    Write-Host 'Saving the secrets in Cloudflare...'
    Put-Secret 'ELEVENLABS_API_KEY' $eleven
    Put-Secret 'ELEVENLABS_VOICE_ID' $VoiceId
    Put-Secret 'ANTHROPIC_API_KEY' $anthropic
    Put-Secret 'ALLOWED_EMAILS' $emails
    $eleven = $null; $anthropic = $null
}

Write-Host 'Deploying...'
$out = npx wrangler deploy 2>&1 | Out-String
Write-Host $out
$url = [regex]::Match($out, 'https://[a-z0-9.-]+\.workers\.dev').Value
if ($url) {
    Write-Host ''
    Write-Host "Done. Server address: $url" -ForegroundColor Green
    Write-Host 'Send that address to Claude to switch Speaking Practice on in the app.' -ForegroundColor Green
} else {
    Write-Host 'Deployed, but the address was not found in the output above. Look for a line ending in workers.dev.' -ForegroundColor Yellow
}
