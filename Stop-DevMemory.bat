@echo off
setlocal

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\stop-devmemory.ps1"
if errorlevel 1 (
  echo.
  echo DevMemory failed to stop cleanly. Press any key to close this window.
  pause >nul
)

endlocal
