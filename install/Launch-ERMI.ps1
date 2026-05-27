$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$ApiPort = 8765
$UiPort = 5173

function Test-Port {
    param([int]$Port)
    return $null -ne (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

function Start-HiddenProcess {
    param(
        [string]$FilePath,
        [string[]]$ArgumentList,
        [string]$WorkingDirectory
    )

    Start-Process -FilePath $FilePath -ArgumentList $ArgumentList -WorkingDirectory $WorkingDirectory -WindowStyle Hidden
}

Push-Location $Root
try {
    if (-not (Test-Port $ApiPort)) {
        Start-HiddenProcess -FilePath "python" -ArgumentList @("-m", "ermi.server", "--root", "archive", "--host", "127.0.0.1", "--port", "$ApiPort") -WorkingDirectory $Root
        Start-Sleep -Seconds 2
    }

    if (-not (Test-Port $UiPort)) {
        $npm = (Get-Command npm.cmd -ErrorAction SilentlyContinue)
        if ($null -eq $npm) {
            $npm = Get-Command npm -ErrorAction Stop
        }
        Start-HiddenProcess -FilePath $npm.Source -ArgumentList @("run", "dev:ui") -WorkingDirectory $Root
        Start-Sleep -Seconds 3
    }

    Start-Process "http://127.0.0.1:$UiPort"
}
finally {
    Pop-Location
}

