$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

Write-Host "ERMI Command Center One-Click Setup" -ForegroundColor Green
Write-Host "Root: $Root"

Write-Step "Installing and repairing local prerequisites"
& "$Root\install\Install-ERMI.ps1" -LaunchAfterInstall

Write-Step "One-click setup complete"
Write-Host "Use the sample paths in the First-Run Setup panel to test ERMI:"
Write-Host "  $Root\sample_data\chatgpt\conversations.json"
Write-Host "  $Root\sample_data\chatlasso\11_SSI_Raw"
