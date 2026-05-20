@echo off
echo ============================================================
echo  CIRO Backend  --  http://0.0.0.0:8000
echo ============================================================

:: Show your local IP so you can enter it in the Flutter app
echo.
echo Your local IP addresses:
ipconfig | findstr /i "IPv4"
echo.
echo Use one of these in the Flutter app's Server Settings (the
echo 192.168.x.x or 10.x.x.x address on your WiFi adapter).
echo ------------------------------------------------------------
echo.

cd /d "%~dp0backend"

:: Activate virtual-env if present
if exist "..\venv\Scripts\activate.bat" (
    call ..\venv\Scripts\activate.bat
) else if exist "..\env\Scripts\activate.bat" (
    call ..\env\Scripts\activate.bat
)

uvicorn main:app --host 0.0.0.0 --port 8000 --reload

pause
