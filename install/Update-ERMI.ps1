$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

Push-Location $Root
try {
    Write-Step "Pulling latest ERMI"
    git pull --ff-only

    Write-Step "Updating Python package"
    python -m pip install -e ".[dev,ml]"

    Write-Step "Updating frontend dependencies"
    npm install

    Write-Step "Running verification"
    python -m pytest -q
    npm run build

    Write-Host ""
    Write-Host "ERMI is up to date." -ForegroundColor Green
}
finally {
    Pop-Location
}

