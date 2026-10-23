@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

echo [1/3] Kiem tra Docker Desktop...
docker info >nul 2>&1
if errorlevel 1 (
    echo     Docker chua chay, dang khoi dong Docker Desktop...
    if exist "C:\Program Files\Docker\Docker\Docker Desktop.exe" (
        start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    ) else (
        echo     Khong tim thay Docker Desktop. Hay mo Docker Desktop thu cong.
        pause
        exit /b 1
    )
    :wait_docker
    timeout /t 3 /nobreak >nul
    docker info >nul 2>&1
    if errorlevel 1 goto wait_docker
)

echo [2/3] Khoi dong ChatBot TLU...
docker compose up -d --build
if errorlevel 1 (
    echo     Khoi dong that bai. Xem loi phia tren.
    pause
    exit /b 1
)

echo [3/3] Cho giao dien san sang...
set count=0
:wait_health
timeout /t 2 /nobreak >nul
powershell -NoProfile -Command "try { Invoke-WebRequest -UseBasicParsing http://localhost:8080/api/health -TimeoutSec 3 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
    set /a count+=1
    if !count! lss 60 goto wait_health
)

start "" http://localhost:8080
echo.
echo Da mo: http://localhost:8080
echo Dang nhap: sinhvien01 / demo-password  hoac  admin01 / demo-password
echo.
pause
