@echo off
setlocal
set ROOT=%~dp0
echo.
echo ERMI Command Center one-click setup
echo Repository: %ROOT%
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%ROOT%install\One-Click-Setup.ps1"
if errorlevel 1 (
  echo.
  echo ERMI one-click setup failed. See the messages above.
  pause
  exit /b 1
)
echo.
echo ERMI is installed and launching.
pause
