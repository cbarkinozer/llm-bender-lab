$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Docker Compose reads .env itself; mirror its non-secret connection settings
# into this process so the importer uses the same credentials.
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^\s*(ARGILLA_(?:API_KEY|WORKSPACE))\s*=\s*(.+?)\s*$') {
            $name = $Matches[1]
            $value = $Matches[2].Trim('"').Trim("'")
            if (-not [Environment]::GetEnvironmentVariable($name, "Process")) {
                [Environment]::SetEnvironmentVariable($name, $value, "Process")
            }
        }
    }
}

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    python -m venv .venv
}
& .\.venv\Scripts\python.exe -m pip install --requirement requirements.txt

docker compose up --detach

$env:ARGILLA_API_URL = "http://127.0.0.1:6900"
if (-not $env:ARGILLA_API_KEY) { $env:ARGILLA_API_KEY = "argilla.apikey" }
if (-not $env:ARGILLA_WORKSPACE) { $env:ARGILLA_WORKSPACE = "sft-review" }

$ready = $false
for ($attempt = 1; $attempt -le 60; $attempt++) {
    try {
        Invoke-WebRequest -UseBasicParsing $env:ARGILLA_API_URL -TimeoutSec 2 | Out-Null
        $ready = $true
        break
    } catch {
        Start-Sleep -Seconds 1
    }
}
if (-not $ready) {
    docker compose logs --tail 100 argilla elasticsearch
    throw "Argilla did not become ready within 60 seconds."
}

& .\.venv\Scripts\python.exe import_candidates.py
if ($LASTEXITCODE -ne 0) {
    throw "Argilla import failed. If this is an existing review session, export it instead of replacing it."
}

Start-Process "http://127.0.0.1:6900"
Write-Host "Argilla is ready at http://127.0.0.1:6900"
Write-Host "Default local login: argilla / 12345678 (change these in .env before any non-local use)."
