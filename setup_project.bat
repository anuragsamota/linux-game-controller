@echo off
setlocal ENABLEDELAYEDEXPANSION

REM Bootstrap the project on Windows.
REM Usage: setup_project.bat [repo_url] [target_dir]

set "DEFAULT_REPO=https://github.com/anuragsamota/librepad-server.git"
set "REPO_URL=%~1"
if "%REPO_URL%"=="" set "REPO_URL=%DEFAULT_REPO%"
set "TARGET_DIR=%~2"

where git >nul 2>nul || (echo [ERROR] Missing required command: git & exit /b 1)
where py >nul 2>nul || where python >nul 2>nul || (echo [ERROR] Missing Python (py or python) & exit /b 1)

if "%REPO_URL%"=="%DEFAULT_REPO%" echo [INFO] No repo URL provided; using default: %DEFAULT_REPO%

if "%TARGET_DIR%"=="" (
  for %%I in ("%REPO_URL%") do set "TARGET_DIR=%%~nI"
)

if exist "%TARGET_DIR%" (
  echo [INFO] Target directory '%TARGET_DIR%' already exists. Skipping clone.
) else (
  echo [INFO] Cloning %REPO_URL% -^> %TARGET_DIR%
  git clone "%REPO_URL%" "%TARGET_DIR%" || exit /b 1
)

cd /d "%TARGET_DIR%" || exit /b 1

echo [INFO] Creating virtual environment: .venv
py -3 -m venv .venv || (python -m venv .venv) || exit /b 1
call .venv\Scripts\activate.bat

echo [INFO] Python: & python -V
echo [INFO] PIP: & pip -V

if exist requirements.txt (
  echo [INFO] Installing requirements.txt
  python -m pip install --upgrade pip
  pip install -r requirements.txt || exit /b 1
) else (
  echo [WARN] requirements.txt not found. Skipping dependency install.
)

if exist web (
  echo [INFO] Installing web client dependencies...
  pushd web
  where pnpm >nul 2>nul
  if %ERRORLEVEL%==0 (
    echo [INFO] Using pnpm for web dependencies
    pnpm install
  ) else (
    where npm >nul 2>nul
    if %ERRORLEVEL%==0 (
      echo [INFO] Using npm for web dependencies
      npm install
    ) else (
      echo [WARN] Neither pnpm nor npm found. Skipping web dependencies.
      echo        Install Node.js and pnpm/npm, then run: cd web ^& pnpm install
    )
  )
  popd
)

echo [INFO] Setup complete. Activate env with: call %CD%\.venv\Scripts\activate.bat

if exist librepadserver.bat (
  echo [INFO] Launching interactive controller manager (librepadserver.bat)
  echo.
  call librepadserver.bat
) else (
  echo [WARN] librepadserver.bat not found. You can start manually later.
)

endlocal
