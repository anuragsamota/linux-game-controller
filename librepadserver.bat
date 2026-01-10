@echo off
setlocal ENABLEDELAYEDEXPANSION

REM LibrePad Server Manager (Windows)
set "SCRIPTS_DIR=%~dp0scripts\windows"
:menu
cls
echo.
echo ==========================================
echo   LIBREPAD SERVER MANAGER (Windows)
echo ==========================================
echo.
echo   1^) init   - Initialize environment (no-op on Windows)
echo   2^) start  - Start WebSocket and Web servers
echo   3^) reset  - Reset environment (no-op on Windows)
echo   4^) help   - Show commands and usage
echo   0^) exit   - Exit
echo.
set /p CHOICE=Enter your choice [0-4]: 

if "%CHOICE%"=="1" goto do_init
if /I "%CHOICE%"=="init" goto do_init
if "%CHOICE%"=="2" goto do_start
if /I "%CHOICE%"=="start" goto do_start
if "%CHOICE%"=="3" goto do_reset
if /I "%CHOICE%"=="reset" goto do_reset
if "%CHOICE%"=="4" goto do_help
if /I "%CHOICE%"=="help" goto do_help
if "%CHOICE%"=="0" goto :eof
echo.
echo [ERROR] Invalid choice. Press any key to continue...
pause >nul
goto menu

:do_init
call "%SCRIPTS_DIR%\init.bat"
echo.
echo [INFO] Press any key to return to menu...
pause >nul
goto menu

:do_start
call "%SCRIPTS_DIR%\start.bat"
goto menu

:do_reset
call "%SCRIPTS_DIR%\reset.bat"
echo.
echo [INFO] Press any key to return to menu...
pause >nul
goto menu

:do_help
cls
echo Usage:
echo   librepadserver.bat ^<command^>
echo.
echo Commands:
echo   init   - Initialize environment (no-op on Windows)
echo   start  - Start WebSocket server and web server
echo   reset  - Reset environment (no-op on Windows)
echo   help   - Show this help
echo.
echo Environment Variables:
echo   WS_HOST  - WebSocket bind address (default: 0.0.0.0)
echo   WS_PORT  - WebSocket port (default: 8765)
echo   WEB_PORT - Web server port (default: 8000)
echo.
echo Press any key to return to menu...
pause >nul
goto menu

endlocal
