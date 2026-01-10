@echo off
setlocal ENABLEDELAYEDEXPANSION

REM Start WebSocket server and static web server (Windows)
set "ROOT_DIR=%~dp0..\.."
set "VENV_DIR=%ROOT_DIR%.venv"

if "%WS_HOST%"=="" set WS_HOST=0.0.0.0
if "%WS_PORT%"=="" set WS_PORT=8765
if "%WEB_PORT%"=="" set WEB_PORT=8000

if exist "%VENV_DIR%\Scripts\activate.bat" (
  echo [INFO] Activating virtual environment at %VENV_DIR%
  call "%VENV_DIR%\Scripts\activate.bat"
) else (
  echo [ERROR] Virtual environment not found at %VENV_DIR%
  echo        Create it with: py -3 -m venv .venv ^& call .venv\Scripts\activate ^& pip install -r requirements.txt
  exit /b 1
)

REM Build web if dist is missing
if not exist "%ROOT_DIR%\web\dist" (
  echo [INFO] Build not found. Building web client...
  pushd "%ROOT_DIR%\web"
  where pnpm >nul 2>nul
  if %ERRORLEVEL%==0 (
    pnpm run build
  ) else (
    where npm >nul 2>nul
    if %ERRORLEVEL%==0 (
      npm run build
    ) else (
      echo [ERROR] Neither pnpm nor npm found. Cannot build web client.
      exit /b 1
    )
  )
  popd
)

echo [INFO] Starting WebSocket server on %WS_HOST%:%WS_PORT%
start "LibrePad WS" cmd /c "set PYTHONPATH=%ROOT_DIR% && py -3 -m src.controller_server.main --host %WS_HOST% --port %WS_PORT%"

echo [INFO] Serving web on http://localhost:%WEB_PORT%
start "LibrePad Web" cmd /c "cd /d \"%ROOT_DIR%\web\dist\" && py -3 -m http.server %WEB_PORT% --bind 0.0.0.0"

echo [INFO] Servers launched in new windows. Press any key to exit this launcher.
pause >nul

endlocal
