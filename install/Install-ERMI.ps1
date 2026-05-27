param(
    [switch]$LaunchAfterInstall,
    [switch]$SkipShortcuts
)

$ErrorActionPreference = "Stop"

$InstallDir = Split-Path -Parent $PSScriptRoot
$Desktop = [Environment]::GetFolderPath("Desktop")
$AppShortcut = Join-Path $Desktop "ERMI Command Center.lnk"
$UpdateShortcut = Join-Path $Desktop "Update ERMI Command Center.lnk"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Test-Command {
    param([string]$Name)
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Install-WingetPackage {
    param(
        [string]$Id,
        [string]$Name
    )

    if (-not (Test-Command winget)) {
        throw "$Name is missing and winget is not available. Install $Name manually, then run this installer again."
    }

    Write-Step "Installing $Name"
    winget install --id $Id --exact --accept-package-agreements --accept-source-agreements
}

function Refresh-Path {
    $machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$machinePath;$userPath"
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

function Ensure-Prerequisites {
    Refresh-Path

    if (-not (Test-Command git)) {
        Install-WingetPackage -Id "Git.Git" -Name "Git"
        Refresh-Path
    }

    if (-not (Test-Command python)) {
        Install-WingetPackage -Id "Python.Python.3.13" -Name "Python 3.13"
        Refresh-Path
    }

    if (-not (Test-Command node) -or -not (Test-Command npm)) {
        Install-WingetPackage -Id "OpenJS.NodeJS.LTS" -Name "Node.js LTS"
        Refresh-Path
    }

    if (-not (Test-Command gh)) {
        Install-WingetPackage -Id "GitHub.cli" -Name "GitHub CLI"
        Refresh-Path
    }
}

function New-Shortcut {
    param(
        [string]$Path,
        [string]$TargetPath,
        [string]$Arguments,
        [string]$WorkingDirectory,
        [string]$Description
    )

    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($Path)
    $shortcut.TargetPath = $TargetPath
    $shortcut.Arguments = $Arguments
    $shortcut.WorkingDirectory = $WorkingDirectory
    $shortcut.Description = $Description
    $shortcut.IconLocation = "$env:SystemRoot\System32\SHELL32.dll,220"
    $shortcut.Save()
}

Write-Host "ERMI Command Center Installer" -ForegroundColor Green
Write-Host "Install directory: $InstallDir"

Ensure-Prerequisites
$python = Resolve-CommandPath -Names @("python.exe", "python") -Fallbacks @("$env:LOCALAPPDATA\Programs\Python\Python313\python.exe")
$npm = Resolve-CommandPath -Names @("npm.cmd", "npm") -Fallbacks @("C:\Program Files\nodejs\npm.cmd")
$env:Path = "$(Split-Path -Parent $npm);$env:Path"

Write-Step "Installing Python package"
Push-Location $InstallDir
try {
    & $python -m pip install --upgrade pip setuptools wheel
    & $python -m pip install -e ".[dev,ml]"

    Write-Step "Installing frontend dependencies"
    & $npm install

    Write-Step "Preparing archive directories"
    & $python -m ermi --root archive init

    Write-Step "Running health diagnostics"
    & $python -m ermi --root archive diagnostics

    if (-not $SkipShortcuts) {
        Write-Step "Creating desktop shortcuts"
        New-Shortcut `
            -Path $AppShortcut `
            -TargetPath "powershell.exe" `
            -Arguments "-NoProfile -ExecutionPolicy Bypass -File `"$InstallDir\install\Launch-ERMI.ps1`"" `
            -WorkingDirectory $InstallDir `
            -Description "Launch ERMI Command Center"

        New-Shortcut `
            -Path $UpdateShortcut `
            -TargetPath "powershell.exe" `
            -Arguments "-NoProfile -ExecutionPolicy Bypass -File `"$InstallDir\install\Update-ERMI.ps1`"" `
            -WorkingDirectory $InstallDir `
            -Description "Update ERMI Command Center"
    }
}
finally {
    Pop-Location
}

Write-Host ""
if (-not $SkipShortcuts) {
    Write-Host "Created shortcuts:" -ForegroundColor Green
    Write-Host "  $AppShortcut"
    Write-Host "  $UpdateShortcut"
}
else {
    Write-Host "Shortcut creation skipped; installer-managed shortcuts will be used." -ForegroundColor Green
}
Write-Host ""
Write-Host "Launch ERMI from the desktop shortcut, or run:"
Write-Host "  npm run api"
Write-Host "  npm run dev:ui"

if ($LaunchAfterInstall) {
    Write-Step "Launching ERMI Command Center"
    & "$InstallDir\install\Launch-ERMI.ps1"
}
