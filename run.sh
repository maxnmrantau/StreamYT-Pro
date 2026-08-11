#!/bin/bash

echo "==============================================================================="
echo "           YouTube Scheduled Stream Server - StreamYT Pro"
echo "==============================================================================="
echo ""

# Cek Python3
if ! command -v python3 &> /dev/null
then
    echo "[ERROR] Python3 tidak ditemukan di sistem!"
    echo "Silakan install Python 3.10+ terlebih dahulu: sudo apt install python3 python3-pip"
    exit 1
fi

# Cek FFmpeg
if ! command -v ffmpeg &> /dev/null
then
    echo "[WARN] FFmpeg tidak terdeteksi di PATH."
    echo "Pastikan ffmpeg terinstall agar live streaming berfungsi: sudo apt install ffmpeg"
    echo ""
fi

# Install / verify dependencies
echo "[1/2] Memeriksa dependensi Python..."
python3 -m pip install -r requirements.txt --quiet

# Start server
echo "[2/2] Memulai server web di http://localhost:8000 ..."
python3 app.py
