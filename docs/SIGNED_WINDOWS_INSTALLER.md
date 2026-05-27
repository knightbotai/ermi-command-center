# Signed Windows Installer Walkthrough

ERMI can be packaged as a Windows setup wizard with Inno Setup.

## What The Installer Does

The installer provides:

- Branded setup wizard graphics.
- Install folder picker.
- Start Menu shortcuts.
- Optional Desktop shortcut checkbox.
- Optional launch-after-install checkbox.
- Dependency install/repair through ERMI's existing PowerShell installer.
- Health diagnostics during install.
- Launch/update shortcuts.

## Build Requirements

Install Inno Setup:

```powershell
winget install --id JRSoftware.InnoSetup --exact
```

Optional signing requirements:

- A real code-signing certificate, usually exported as `.pfx`.
- Windows SDK signing tools, specifically `signtool.exe`.
- A timestamp server such as `http://timestamp.digicert.com`.

Install Windows SDK signing tools when you want `-Sign` or `-DevSelfSign`:

```powershell
winget install --id Microsoft.WindowsSDK.10.0.18362 --exact
```

## Build Unsigned Installer

From the repo root:

```powershell
.\install\Build-WindowsInstaller.ps1
```

Output:

```text
installer\output\ERMI-Command-Center-Setup-0.1.0-mvp.exe
```

If Inno Setup is missing and you want the script to install it:

```powershell
.\install\Build-WindowsInstaller.ps1 -InstallTooling
```

## Build Signed Installer

With a `.pfx` certificate:

```powershell
.\install\Build-WindowsInstaller.ps1 `
  -Sign `
  -CertificatePath C:\path\to\codesign.pfx `
  -CertificatePassword "certificate-password"
```

With a certificate already installed in the Windows certificate store:

```powershell
Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert

.\install\Build-WindowsInstaller.ps1 `
  -Sign `
  -CertificateThumbprint CERT_THUMBPRINT_HERE
```

The script compiles the installer first, then signs the final `.exe` with SHA-256 and a timestamp.

## Build Internal Dev-Signed Installer

For private testing on machines you control:

```powershell
.\install\Build-WindowsInstaller.ps1 -DevSelfSign
```

This creates or reuses a local development code-signing certificate:

```text
CN=ERMI Command Center Dev Signing
```

It signs the installer and exports the public certificate beside the installer:

```text
installer\output\ERMI-Dev-Signing-Certificate.cer
```

To trust that dev-signed installer on one of your own machines, import the `.cer` into:

```text
Trusted Root Certification Authorities
Trusted Publishers
```

Only do this on machines you control. This is useful for rehearsing the signed-installer workflow; it is not public distribution trust.

Until the dev certificate is trusted on the target machine, Windows will show the signature chain as untrusted even though the installer file is signed. That is expected for internal self-signing.

## Checksums

Every installer build writes:

```text
installer\output\ERMI-Command-Center-Setup-0.1.0-mvp.exe.sha256.txt
```

Publish that checksum beside release installers so users can verify the downloaded file.

## Recommended Release Flow

1. Run tests and build:

```powershell
python -m pytest -q
npm run build
```

2. Build installer:

```powershell
.\install\Build-WindowsInstaller.ps1 -InstallTooling
```

3. Sign installer when certificate is available:

```powershell
.\install\Build-WindowsInstaller.ps1 -Sign -CertificatePath C:\path\to\codesign.pfx -CertificatePassword "..."
```

4. Test install on a clean Windows profile or VM.

5. Publish the installer as a GitHub Release asset attached to:

```text
v0.1.0-mvp
```

## Certificate Notes

For real distribution, use an OV or EV code-signing certificate from a trusted certificate authority. Self-signed certificates are useful only for internal testing; Windows SmartScreen will not trust them like a commercial certificate.

Current local status: no code-signing certificate is installed in `Cert:\CurrentUser\My` by default. The build pipeline can produce an unsigned installer immediately and a signed installer as soon as a certificate is available.

## Design Notes

The installer visuals follow ERMI's command-center style:

- Dark local-operations palette.
- Cyan system-health accent.
- Minimal wizard copy.
- Practical options instead of decorative steps.
- Install, diagnose, launch as the central flow.
