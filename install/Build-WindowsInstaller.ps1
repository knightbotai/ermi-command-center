param(
    [string]$AppVersion = "0.1.0-mvp",
    [switch]$InstallTooling,
    [switch]$Sign,
    [switch]$DevSelfSign,
    [string]$CertificatePath = "",
    [string]$CertificatePassword = "",
    [string]$CertificateThumbprint = "",
    [string]$DevCertificateSubject = "CN=ERMI Command Center Dev Signing",
    [string]$TimestampUrl = "http://timestamp.digicert.com",
    [switch]$CheckOnly
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$InstallerRoot = Join-Path $Root "installer"
$GeneratedAssets = Join-Path $InstallerRoot "assets\generated"
$InnoScript = Join-Path $InstallerRoot "ERMI-Command-Center.iss"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Find-InnoCompiler {
    $command = Get-Command iscc.exe -ErrorAction SilentlyContinue
    if ($null -ne $command) {
        return $command.Source
    }

    $candidates = @(
        "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
    )
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }
    return $null
}

function Find-SignTool {
    $command = Get-Command signtool.exe -ErrorAction SilentlyContinue
    if ($null -ne $command) {
        return $command.Source
    }

    $kits = "${env:ProgramFiles(x86)}\Windows Kits\10\bin"
    if (Test-Path $kits) {
        $candidate = Get-ChildItem -Path $kits -Recurse -Filter signtool.exe -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -like "*\x64\signtool.exe" } |
            Sort-Object FullName -Descending |
            Select-Object -First 1
        if ($null -ne $candidate) {
            return $candidate.FullName
        }
    }
    return $null
}

function Get-OrCreateDevCertificate {
    param([string]$Subject)

    $cert = Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert |
        Where-Object { $_.Subject -eq $Subject } |
        Sort-Object NotAfter -Descending |
        Select-Object -First 1

    if ($null -ne $cert) {
        return $cert
    }

    Write-Step "Creating internal development signing certificate"
    return New-SelfSignedCertificate `
        -Type CodeSigningCert `
        -Subject $Subject `
        -CertStoreLocation Cert:\CurrentUser\My `
        -KeyAlgorithm RSA `
        -KeyLength 3072 `
        -HashAlgorithm SHA256 `
        -KeyExportPolicy Exportable `
        -NotAfter (Get-Date).AddYears(2)
}

function Export-DevCertificate {
    param(
        [System.Security.Cryptography.X509Certificates.X509Certificate2]$Certificate,
        [string]$OutputDirectory
    )

    $certPath = Join-Path $OutputDirectory "ERMI-Dev-Signing-Certificate.cer"
    Export-Certificate -Cert $Certificate -FilePath $certPath | Out-Null
    return $certPath
}

function Write-InstallerChecksum {
    param([string]$Installer)

    $hash = Get-FileHash -Algorithm SHA256 -Path $Installer
    $checksumPath = "$Installer.sha256.txt"
    "$($hash.Hash)  $(Split-Path -Leaf $Installer)" | Set-Content -Path $checksumPath -Encoding ASCII
    return $checksumPath
}

function Ensure-GeneratedAssets {
    Write-Step "Generating installer bitmap and icon assets"
    New-Item -ItemType Directory -Force -Path $GeneratedAssets | Out-Null

    Add-Type -AssemblyName System.Drawing

    $banner = New-Object System.Drawing.Bitmap 497, 58
    $graphics = [System.Drawing.Graphics]::FromImage($banner)
    $graphics.Clear([System.Drawing.ColorTranslator]::FromHtml("#071014"))
    $cyan = [System.Drawing.ColorTranslator]::FromHtml("#35d7ee")
    $text = [System.Drawing.ColorTranslator]::FromHtml("#edf7f8")
    $muted = [System.Drawing.ColorTranslator]::FromHtml("#8fa1a8")
    $graphics.FillRectangle((New-Object System.Drawing.SolidBrush $cyan), 0, 56, 497, 2)
    $graphics.DrawEllipse((New-Object System.Drawing.Pen $cyan, 3), 16, 14, 30, 30)
    $graphics.DrawString("ERMI Command Center", ([System.Drawing.Font]::new("Segoe UI", 18.0, [System.Drawing.FontStyle]::Bold)), (New-Object System.Drawing.SolidBrush $text), 58, 9)
    $graphics.DrawString("Local-first memory archive, diagnostics, recall, and backup workflow", ([System.Drawing.Font]::new("Segoe UI", 9.0)), (New-Object System.Drawing.SolidBrush $muted), 58, 35)
    $banner.Save((Join-Path $GeneratedAssets "wizard-banner.bmp"), [System.Drawing.Imaging.ImageFormat]::Bmp)
    $graphics.Dispose()
    $banner.Dispose()

    $side = New-Object System.Drawing.Bitmap 164, 314
    $graphics = [System.Drawing.Graphics]::FromImage($side)
    $graphics.Clear([System.Drawing.ColorTranslator]::FromHtml("#061015"))
    $graphics.FillRectangle((New-Object System.Drawing.SolidBrush $cyan), 0, 0, 6, 314)
    $graphics.DrawEllipse((New-Object System.Drawing.Pen $cyan, 4), 47, 41, 70, 70)
    $graphics.DrawString("ERMI", ([System.Drawing.Font]::new("Segoe UI", 22.0, [System.Drawing.FontStyle]::Bold)), (New-Object System.Drawing.SolidBrush $text), 52, 132)
    $graphics.DrawString("Command Center", ([System.Drawing.Font]::new("Segoe UI", 9.0)), (New-Object System.Drawing.SolidBrush $muted), 43, 165)
    $graphics.DrawString("LOCAL MVP", ([System.Drawing.Font]::new("Segoe UI", 11.0, [System.Drawing.FontStyle]::Bold)), (New-Object System.Drawing.SolidBrush $cyan), 49, 230)
    $side.Save((Join-Path $GeneratedAssets "wizard-side.bmp"), [System.Drawing.Imaging.ImageFormat]::Bmp)
    $graphics.Dispose()
    $side.Dispose()

    $iconBitmap = New-Object System.Drawing.Bitmap 64, 64
    $graphics = [System.Drawing.Graphics]::FromImage($iconBitmap)
    $graphics.Clear([System.Drawing.ColorTranslator]::FromHtml("#071014"))
    $graphics.DrawEllipse((New-Object System.Drawing.Pen $cyan, 5), 12, 12, 40, 40)
    $graphics.DrawLine((New-Object System.Drawing.Pen $cyan, 5), 24, 32, 40, 32)
    $graphics.DrawLine((New-Object System.Drawing.Pen $cyan, 5), 32, 24, 32, 40)
    $handle = $iconBitmap.GetHicon()
    $icon = [System.Drawing.Icon]::FromHandle($handle)
    $stream = [System.IO.File]::Create((Join-Path $GeneratedAssets "ermi.ico"))
    $icon.Save($stream)
    $stream.Close()
    $icon.Dispose()
    $graphics.Dispose()
    $iconBitmap.Dispose()
}

function Install-InnoSetup {
    if (-not $InstallTooling) {
        return
    }
    Write-Step "Installing Inno Setup"
    winget install --id JRSoftware.InnoSetup --exact --accept-package-agreements --accept-source-agreements
}

Push-Location $Root
try {
    Ensure-GeneratedAssets
    Install-InnoSetup

    $iscc = Find-InnoCompiler
    if ($null -eq $iscc) {
        if ($CheckOnly) {
            Write-Host "Inno Setup compiler not installed. Install with:" -ForegroundColor Yellow
            Write-Host "  winget install --id JRSoftware.InnoSetup --exact"
            return
        }
        throw "Inno Setup compiler not found. Re-run with -InstallTooling or install JRSoftware.InnoSetup."
    }

    if ($CheckOnly) {
        Write-Host "Installer prerequisites look ready." -ForegroundColor Green
        Write-Host "Inno compiler: $iscc"
        return
    }

    Write-Step "Compiling ERMI Windows installer"
    & $iscc "/DAppVersion=$AppVersion" $InnoScript

    $installer = Join-Path $InstallerRoot "output\ERMI-Command-Center-Setup-$AppVersion.exe"
    if (-not (Test-Path $installer)) {
        throw "Expected installer was not created: $installer"
    }

    if ($DevSelfSign) {
        Write-Step "Signing installer with internal development certificate"
        $cert = Get-OrCreateDevCertificate -Subject $DevCertificateSubject
        $signtool = Find-SignTool
        if ($null -eq $signtool) {
            throw "signtool.exe not found. Install Windows SDK signing tools."
        }
        & $signtool sign /sha1 $cert.Thumbprint /tr $TimestampUrl /td sha256 /fd sha256 $installer
        $publicCert = Export-DevCertificate -Certificate $cert -OutputDirectory (Split-Path -Parent $installer)
        Write-Host "Development public certificate exported:" -ForegroundColor Yellow
        Write-Host "  $publicCert"
        Write-Host "Trust it only on machines you control."
    }
    elseif ($Sign) {
        Write-Step "Signing installer"
        $signtool = Find-SignTool
        if ($null -eq $signtool) {
            throw "signtool.exe not found. Install Windows SDK signing tools."
        }
        if ($CertificateThumbprint) {
            & $signtool sign /sha1 $CertificateThumbprint /tr $TimestampUrl /td sha256 /fd sha256 $installer
        }
        elseif ($CertificatePath) {
            & $signtool sign /f $CertificatePath /p $CertificatePassword /tr $TimestampUrl /td sha256 /fd sha256 $installer
        }
        else {
            throw "CertificatePath or CertificateThumbprint is required when -Sign is used."
        }
    }

    Write-Step "Writing SHA-256 checksum"
    $checksum = Write-InstallerChecksum -Installer $installer

    Write-Host ""
    Write-Host "Installer ready:" -ForegroundColor Green
    Write-Host "  $installer"
    Write-Host "Checksum:"
    Write-Host "  $checksum"
}
finally {
    Pop-Location
}
