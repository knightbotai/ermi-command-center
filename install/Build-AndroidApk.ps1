param(
    [switch]$InstallTooling,
    [switch]$OpenAndroidProject
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Assert-LastCommand {
    param([string]$Message)
    if ($LASTEXITCODE -ne 0) {
        throw $Message
    }
}

function Test-Command {
    param([string]$Name)
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Resolve-Jdk {
    $candidates = @(
        $env:JAVA_HOME,
        "C:\Program Files\Eclipse Adoptium\jdk-21.0.11.10-hotspot",
        "C:\Program Files\Eclipse Adoptium\jdk-21.0.10.9-hotspot"
    ) | Where-Object { $_ }

    $adoptiumRoot = "C:\Program Files\Eclipse Adoptium"
    if (Test-Path $adoptiumRoot) {
        $candidates += Get-ChildItem $adoptiumRoot -Directory -Filter "jdk-*" |
            Sort-Object Name -Descending |
            ForEach-Object { $_.FullName }
    }

    foreach ($candidate in $candidates | Select-Object -Unique) {
        $java = Join-Path $candidate "bin\java.exe"
        if (-not (Test-Path $java)) {
            continue
        }
        $versionOutput = cmd /c "`"$java`" -version 2>&1"
        $versionLine = ($versionOutput | Select-Object -First 1).ToString()
        if ($versionLine -match 'version "(\d+)') {
            $major = [int]$Matches[1]
            if ($major -ge 17) {
                return @{
                    Home = $candidate
                    Java = $java
                    Major = $major
                }
            }
        }
    }
    return $null
}

function Install-PackageIfMissing {
    param(
        [string]$Command,
        [string]$WingetId,
        [string]$Name
    )

    if (Test-Command $Command) {
        return
    }
    if (-not $InstallTooling) {
        throw "$Name is missing. Re-run with -InstallTooling or install $WingetId."
    }
    Write-Step "Installing $Name"
    winget install --id $WingetId --exact --accept-package-agreements --accept-source-agreements
}

function Resolve-AndroidSdk {
    $candidates = @(
        $env:ANDROID_HOME,
        $env:ANDROID_SDK_ROOT,
        (Join-Path $env:LOCALAPPDATA "Android\Sdk")
    ) | Where-Object { $_ }

    foreach ($candidate in $candidates | Select-Object -Unique) {
        if (Test-Path (Join-Path $candidate "cmdline-tools\latest\bin\sdkmanager.bat")) {
            return $candidate
        }
    }
    return $null
}

function Install-AndroidSdk {
    if (-not $InstallTooling) {
        throw "Android SDK command-line tools are missing. Re-run with -InstallTooling."
    }

    $sdkRoot = Join-Path $env:LOCALAPPDATA "Android\Sdk"
    $toolsRoot = Join-Path $sdkRoot "cmdline-tools"
    $latestRoot = Join-Path $toolsRoot "latest"
    $downloadUrl = "https://dl.google.com/android/repository/commandlinetools-win-14742923_latest.zip"
    $zipPath = Join-Path $env:TEMP "android-commandlinetools-latest.zip"
    $extractRoot = Join-Path $env:TEMP "android-commandlinetools-latest"

    Write-Step "Installing Android SDK command-line tools"
    New-Item -ItemType Directory -Force -Path $toolsRoot | Out-Null
    if (Test-Path $extractRoot) {
        Remove-Item -Recurse -Force $extractRoot
    }
    Invoke-WebRequest -Uri $downloadUrl -OutFile $zipPath
    Expand-Archive -Path $zipPath -DestinationPath $extractRoot -Force
    if (Test-Path $latestRoot) {
        Remove-Item -Recurse -Force $latestRoot
    }
    Move-Item -Path (Join-Path $extractRoot "cmdline-tools") -Destination $latestRoot
    return $sdkRoot
}

function Invoke-SdkManager {
    param(
        [string]$SdkRoot,
        [string[]]$Packages
    )

    $sdkManager = Join-Path $SdkRoot "cmdline-tools\latest\bin\sdkmanager.bat"
    if (-not (Test-Path $sdkManager)) {
        throw "sdkmanager not found at $sdkManager"
    }

    Write-Step "Accepting Android SDK licenses"
    $yesLines = 1..80 | ForEach-Object { "y" }
    $yesLines | & $sdkManager --sdk_root=$SdkRoot --licenses
    if ($LASTEXITCODE -ne 0) {
        throw "Android SDK license acceptance failed."
    }

    Write-Step "Installing Android SDK packages"
    & $sdkManager --sdk_root=$SdkRoot @Packages
    if ($LASTEXITCODE -ne 0) {
        throw "Android SDK package installation failed."
    }
}

function Resolve-Npm {
    $npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if ($null -ne $npm) {
        return $npm.Source
    }
    $fallback = "C:\Program Files\nodejs\npm.cmd"
    if (Test-Path $fallback) {
        return $fallback
    }
    throw "npm not found. Install Node.js LTS."
}

Push-Location $Root
try {
    $jdk = Resolve-Jdk
    if ($null -eq $jdk) {
        if (-not $InstallTooling) {
            throw "JDK 17+ is missing. Re-run with -InstallTooling or install EclipseAdoptium.Temurin.21.JDK."
        }
        Write-Step "Installing Temurin JDK 21"
        winget install --id EclipseAdoptium.Temurin.21.JDK --exact --accept-package-agreements --accept-source-agreements --disable-interactivity
        $jdk = Resolve-Jdk
        if ($null -eq $jdk) {
            throw "JDK 21 installed, but this shell could not find it. Open a new PowerShell window and rerun this script."
        }
    }
    $env:JAVA_HOME = $jdk.Home
    $env:Path = "$(Join-Path $jdk.Home "bin");$env:Path"
    Write-Step "Using JDK $($jdk.Major) at $($jdk.Home)"

    $sdkRoot = Resolve-AndroidSdk
    if ($null -eq $sdkRoot) {
        $sdkRoot = Install-AndroidSdk
    }
    $env:ANDROID_HOME = $sdkRoot
    $env:ANDROID_SDK_ROOT = $sdkRoot
    $env:Path = "$(Join-Path $sdkRoot "platform-tools");$(Join-Path $sdkRoot "cmdline-tools\latest\bin");$env:Path"
    Invoke-SdkManager -SdkRoot $sdkRoot -Packages @("platform-tools", "platforms;android-36", "build-tools;36.0.0")
    Write-Step "Using Android SDK at $sdkRoot"

    $npm = Resolve-Npm
    $env:Path = "$(Split-Path -Parent $npm);$env:Path"

    Write-Step "Installing JavaScript dependencies"
    & $npm install
    Assert-LastCommand "npm install failed."

    Write-Step "Building ERMI mobile web bundle"
    & $npm run build:android:web
    Assert-LastCommand "Android web bundle build failed."

    if (-not (Test-Path (Join-Path $Root "android"))) {
        Write-Step "Creating Capacitor Android project"
        & $npm run android:add
        Assert-LastCommand "Capacitor Android project creation failed."
    }

    Write-Step "Syncing Capacitor Android project"
    & $npm run android:sync
    Assert-LastCommand "Capacitor Android sync failed."

    $localProperties = Join-Path $Root "android\local.properties"
    "sdk.dir=$($sdkRoot.Replace('\', '/'))" | Set-Content -Encoding ascii -Path $localProperties

    if ($OpenAndroidProject) {
        Write-Step "Opening Android project"
        & $npm run android:open
        Assert-LastCommand "Opening Android project failed."
    }

    $gradlew = Join-Path $Root "android\gradlew.bat"
    if (Test-Path $gradlew) {
        Write-Step "Building sideload debug APK"
        Push-Location (Join-Path $Root "android")
        try {
            & ".\gradlew.bat" assembleDebug
            if ($LASTEXITCODE -ne 0) {
                throw "Gradle APK build failed."
            }
        }
        finally {
            Pop-Location
        }
        Write-Host ""
        Write-Host "APK ready:" -ForegroundColor Green
        $apk = Join-Path $Root "android\app\build\outputs\apk\debug\app-debug.apk"
        $hashPath = "$apk.sha256.txt"
        $hash = (Get-FileHash $apk -Algorithm SHA256).Hash
        "$hash  app-debug.apk" | Set-Content -Encoding ascii -Path $hashPath
        Write-Host "  $apk"
        Write-Host "  $hashPath"
        Write-Host "  SHA256: $hash"
    }
    else {
        Write-Host "Android project synced. Install Android Studio/SDK, then run this script again to build the APK." -ForegroundColor Yellow
    }
}
finally {
    Pop-Location
}
