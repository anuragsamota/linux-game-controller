@echo off
setlocal ENABLEDELAYEDEXPANSION

REM Build the React web client for production (Windows)
set "ROOT_DIR=%~dp0..\..\"
set "WEB_DIR=%ROOT_DIR%web"

echo [INFO] Building web client for production...

cd /d "%WEB_DIR%" || (echo [ERROR] Failed to cd into %WEB_DIR% & exit /b 1)

where pnpm >nul 2>nul
if %ERRORLEVEL%==0 (
  set "PKG_MANAGER=pnpm"
) else (
  where npm >nul 2>nul
  if %ERRORLEVEL%==0 (
    set "PKG_MANAGER=npm"
  ) else (
    echo [ERROR] Neither pnpm nor npm found. Please install Node.js package manager.
    exit /b 1
  )
)

echo [INFO] Using package manager: %PKG_MANAGER%

if not exist node_modules (
  echo [INFO] Installing dependencies...
  %PKG_MANAGER% install
  if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%
)

echo [INFO] Running production build...
%PKG_MANAGER% run build
if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

echo.
echo ==========================================
echo Build Complete!
echo ==========================================
echo Output directory: %WEB_DIR%\dist
echo.
echo To serve production build:
echo   cd %WEB_DIR%\dist ^&^& py -m http.server 8000
echo ==========================================

endlocal
