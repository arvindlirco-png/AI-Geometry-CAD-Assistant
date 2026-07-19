@echo off
setlocal

set "ROOT=%~dp0"
cd /d "%ROOT%"

echo Starting AI Geometry CAD Assistant...
echo.

where ollama >nul 2>nul
if errorlevel 1 (
  echo [WARN] Ollama command not found. Backend will still start and use rule parser fallback.
) else (
  powershell -NoProfile -ExecutionPolicy Bypass -Command "try { Invoke-WebRequest -UseBasicParsing http://127.0.0.1:11434/api/tags -TimeoutSec 2 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>nul
  if errorlevel 1 (
    echo Starting Ollama...
    start "Ollama Server" cmd /k "ollama serve"
    timeout /t 3 /nobreak >nul
  ) else (
    echo Ollama is already running.
  )
)

echo Starting backend on http://127.0.0.1:8020 ...
start "AI ChatCAD Backend" cmd /k "cd /d ""%ROOT%backend"" && call run_backend.bat"

timeout /t 3 /nobreak >nul

echo Starting frontend on http://127.0.0.1:5175 ...
start "AI ChatCAD Frontend" cmd /k "cd /d ""%ROOT%frontend"" && call run_frontend.bat"

timeout /t 5 /nobreak >nul

echo Opening app...
start "" "http://127.0.0.1:5175"

echo.
echo Started:
echo   Ollama:  http://127.0.0.1:11434
echo   Backend: http://127.0.0.1:8020
echo   App:     http://127.0.0.1:5175
echo.
echo Keep the Backend and Frontend windows open while using the app.
pause
