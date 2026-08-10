@echo off
title YouTube Scheduled Stream Server (StreamYT Pro)
color 0A

echo ===============================================================================
echo            YouTube Scheduled Stream Server - StreamYT Pro
echo ===============================================================================
echo.

:: Cek Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python tidak ditemukan di sistem PATH!
    echo Silakan install Python 3.10+ terlebih dahulu.
    pause
    exit /b
)

:: Cek FFmpeg
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] FFmpeg tidak terdeteksi di sistem PATH.
    echo Pastikan ffmpeg.exe dapat diakses agar live streaming berfungsi.
    echo.
)

:: Install / verify dependencies
echo [1/2] Memeriksa dependensi Python...
pip install -r requirements.txt --quiet

:: Start server and open browser
echo [2/2] Memulai server web di http://localhost:8000 ...
echo [INFO] Ikon aplikasi aktif di System Tray (Pojok kanan bawah taskbar).
echo [INFO] Anda dapat menyembunyikan jendela CMD ini kapan saja via tombol di Web / Tray Icon.
start "" "http://localhost:8000"

python app.py
pause
