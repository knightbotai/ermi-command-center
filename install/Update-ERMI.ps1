$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Resolve-CommandPath {
    param(
        [string[]]$Names,
        [string[]]$Fallbacks
    )

    foreach ($name in $Names) {
        $command = Get-Command $name -ErrorAction SilentlyContinue
        if ($null -ne $command) {
            return $command.Source
        }
    }
    foreach ($path in $Fallbacks) {
        if (Test-Path $path) {
            return $path
        }
    }
    throw "Unable to find any of: $($Names -join ', ')"
}

Push-Location $Root
try {
    $python = Resolve-CommandPath -Names @("python.exe", "python") -Fallbacks @("$env:LOCALAPPDATA\Programs\Python\Python313\python.exe")
    $npm = Resolve-CommandPath -Names @("npm.cmd", "npm") -Fallbacks @("C:\Program Files\nodejs\npm.cmd")
    $env:Path = "$(Split-Path -Parent $npm);$env:Path"

    Write-Step "Pulling latest ERMI"
    git pull --ff-only

    Write-Step "Updating Python package"
    & $python -m pip install -e ".[dev,ml]"

    Write-Step "Updating frontend dependencies"
    & $npm install

    Write-Step "Running migrations"
    & $python -m ermi --root archive migrate

    Write-Step "Running verification"
    & $python -m pytest -q
    & $npm run build

    Write-Host ""
    Write-Host "ERMI is up to date." -ForegroundColor Green
}
finally {
    Pop-Location
}
