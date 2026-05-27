@echo off
setlocal
set SCRIPT_DIR=%~dp0
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%Install-ERMI.ps1"
if errorlevel 1 (
  echo.
  echo ERMI installation failed. See the messages above.
  pause
  exit /b 1
)
echo.
echo ERMI installation complete.
pause

