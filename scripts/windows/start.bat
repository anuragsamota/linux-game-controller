@echo off
setlocal ENABLEDELAYEDEXPANSION

REM Start LibrePad servers with flexible configuration (Windows)
REM - WebSocket server (game controller): src/controller_server/main.py
REM - UDP server (native clients): Built into controller_server/main.py
REM - Web client server (static files): Python HTTP server
REM
REM Usage: start.bat [SERVICE_MODE]
REM SERVICE_MODE:
REM   all       - Start WebSocket, UDP, and Web (default)
REM   ws        - Start only WebSocket server
REM   udp       - Start only UDP server  
REM   web       - Start only Web server
REM   ws-web    - Start WebSocket and Web (no UDP)

set "ROOT_DIR=%~dp0..\.."
set "VENV_DIR=%ROOT_DIR%.venv"
set "SERVICE_MODE=%1"

REM Default to 'all' if no mode specified
if "%SERVICE_MODE%"=="" set SERVICE_MODE=all

REM Validate service mode
if not "%SERVICE_MODE%"=="all" if not "%SERVICE_MODE%"=="ws" if not "%SERVICE_MODE%"=="udp" if not "%SERVICE_MODE%"=="web" if not "%SERVICE_MODE%"=="ws-web" (
	echo [ERROR] Invalid service mode: %SERVICE_MODE%
	echo [INFO] Valid modes: all, ws, udp, web, ws-web
	exit /b 1
)

if "%WS_HOST%"=="" set WS_HOST=0.0.0.0
if "%WS_PORT%"=="" set WS_PORT=8765
if "%UDP_PORT%"=="" set UDP_PORT=9775
if "%WEB_PORT%"=="" set WEB_PORT=8000

if exist "%VENV_DIR%\Scripts\activate.bat" (
  echo [INFO] Activating virtual environment at %VENV_DIR%
  call "%VENV_DIR%\Scripts\activate.bat"
) else (
  echo [ERROR] Virtual environment not found at %VENV_DIR%
  echo        Create it with: py -3 -m venv .venv ^& call .venv\Scripts\activate ^& pip install -r requirements.txt
  exit /b 1
)

REM Build web if dist is missing and we need to start web
if "%SERVICE_MODE%"=="all" goto build_web
if "%SERVICE_MODE%"=="web" goto build_web
if "%SERVICE_MODE%"=="ws-web" goto build_web
goto skip_build_web

:build_web
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

:skip_build_web
echo.
echo ==========================================
echo ^[INFO^] LibrePad Server Starting
echo ==========================================
echo Service Mode: %SERVICE_MODE%
echo.

REM Start WebSocket/UDP server
if "%SERVICE_MODE%"=="all" goto start_ws
if "%SERVICE_MODE%"=="ws" goto start_ws
if "%SERVICE_MODE%"=="udp" goto start_ws
if "%SERVICE_MODE%"=="ws-web" goto start_ws
goto skip_ws

:start_ws
echo [INFO] Starting WebSocket server on %WS_HOST%:%WS_PORT% (UDP on %UDP_PORT%)
start "LibrePad WS+UDP" cmd /c "set PYTHONPATH=%ROOT_DIR% && py -3 -m src.controller_server.main --host %WS_HOST% --port %WS_PORT% --udp-port %UDP_PORT%"
timeout /t 2 /nobreak >nul

:skip_ws

REM Start Web server
if "%SERVICE_MODE%"=="all" goto start_web
if "%SERVICE_MODE%"=="web" goto start_web
if "%SERVICE_MODE%"=="ws-web" goto start_web
goto skip_web

:start_web
echo [INFO] Serving web on http://localhost:%WEB_PORT%
start "LibrePad Web" cmd /c "cd /d \"%ROOT_DIR%\web\dist\" && py -3 -m http.server %WEB_PORT% --bind 0.0.0.0"
timeout /t 2 /nobreak >nul

:skip_web

echo.
echo ==========================================
echo ^[INFO^] LibrePad Servers
echo ==========================================

REM Display active services
if "%SERVICE_MODE%"=="all" (
	echo WebSocket Endpoint: ws://%WS_HOST%:%WS_PORT%
	echo UDP Endpoint: udp://%WS_HOST%:%UDP_PORT%
	echo Web Server: http://localhost:%WEB_PORT%
)
if "%SERVICE_MODE%"=="ws" (
	echo WebSocket Endpoint: ws://%WS_HOST%:%WS_PORT%
)
if "%SERVICE_MODE%"=="udp" (
	echo UDP Endpoint: udp://%WS_HOST%:%UDP_PORT%
)
if "%SERVICE_MODE%"=="web" (
	echo Web Server: http://localhost:%WEB_PORT%
)
if "%SERVICE_MODE%"=="ws-web" (
	echo WebSocket Endpoint: ws://%WS_HOST%:%WS_PORT%
	echo Web Server: http://localhost:%WEB_PORT%
)

echo ==========================================
echo [INFO] Servers launched. Press any key to exit this launcher.
pause >nul

endlocal
