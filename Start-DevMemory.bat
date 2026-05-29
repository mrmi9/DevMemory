@echo off
setlocal

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start-devmemory.ps1"
if errorlevel 1 (
  echo.
  echo DevMemory failed to start. Press any key to close this window.
  pause >nul
)

endlocal
