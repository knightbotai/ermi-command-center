$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$ApiPort = 8765
$UiPort = 5173

function Test-Port {
    param([int]$Port)
    return $null -ne (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

function Stop-PortListeners {
    param([int[]]$Ports)

    foreach ($port in $Ports) {
        $listeners = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
        foreach ($listener in $listeners) {
            try {
                Stop-Process -Id $listener.OwningProcess -Force -ErrorAction Stop
                Start-Sleep -Milliseconds 300
            }
            catch {
                Write-Host "Could not stop process $($listener.OwningProcess) on port $port: $($_.Exception.Message)" -ForegroundColor Yellow
            }
        }
    }
}

function Start-HiddenProcess {
    param(
        [string]$FilePath,
        [string[]]$ArgumentList,
        [string]$WorkingDirectory
    )

    Start-Process -FilePath $FilePath -ArgumentList $ArgumentList -WorkingDirectory $WorkingDirectory -WindowStyle Hidden
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

    Stop-PortListeners -Ports @($ApiPort, $UiPort)

    if (-not (Test-Port $ApiPort)) {
        Start-HiddenProcess -FilePath $python -ArgumentList @("-m", "ermi.server", "--root", "archive", "--host", "127.0.0.1", "--port", "$ApiPort") -WorkingDirectory $Root
        Start-Sleep -Seconds 2
    }

    if (-not (Test-Port $UiPort)) {
        Start-HiddenProcess -FilePath $npm -ArgumentList @("run", "dev:ui") -WorkingDirectory $Root
        Start-Sleep -Seconds 3
    }

    Start-Process "http://127.0.0.1:$UiPort"
}
finally {
    Pop-Location
}
