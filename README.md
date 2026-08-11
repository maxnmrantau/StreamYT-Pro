<img width="947" height="712" alt="image" src="https://github.com/user-attachments/assets/cf27462a-dcac-4b91-ac11-f204d03a8c13" />

<div align="center">

# StreamYT Pro
### **Automated 24/7 Scheduled YouTube Live Streaming Server (Cross-Platform)**

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Framework-FastAPI-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![FFmpeg](https://img.shields.io/badge/Engine-FFmpeg-007808.svg?logo=ffmpeg&logoColor=white)](https://ffmpeg.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-informational.svg)](https://github.com/maxnmrantau/StreamYT-Pro)
[![Telegram](https://img.shields.io/badge/Notifications-Telegram%20Bot-2CA5E0.svg?logo=telegram&logoColor=white)](https://telegram.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

*A modern, lightweight, and robust local streaming scheduler that automatically broadcasts your local video files to YouTube Live on exact schedules, without needing OBS Studio open.*

[Fitur Utama](#-fitur-utama) • [Cara Instalasi](#-cara-instalasi--menjalankan) • [Panduan Linux & VPS](#-panduan-penggunaan-di-linux--vps-server) • [Panduan Penggunaan](#-panduan-penggunaan) • [Mode Durasi](#-penjelasan-mode-durasi-a-b-c) • [Notifikasi Telegram](#-panduan-notifikasi-telegram) • [System Tray](#-system-tray--shortcut-taskbar) • [Lisensi](#-lisensi)

---

</div>

## 📖 Apa itu StreamYT Pro?

**StreamYT Pro** adalah aplikasi server berbasis **FastAPI** dan **FFmpeg** yang dirancang khusus untuk kreator konten, podcaster, dan pengelola channel YouTube yang ingin menyiarkan video rekaman ke YouTube Live secara otomatis dan terjadwal 24/7 langsung dari PC Windows atau Server VPS Linux.

Tidak seperti OBS Studio yang berat dan memerlukan konfigurasi manual setiap sesi, **StreamYT Pro**:
* **Ringan & Senyap**: Berjalan sangat efisien di latar belakang (*background service / system tray*).
* **Multi-Platform**: Mendukung **Windows** (dengan System Tray & shortcut) dan **Linux / VPS Headless** (dengan `run.sh` / `systemd`).
* **Jadwal Presisi**: Memiliki penjadwal otomatis berbasis waktu lokal dengan proteksi bentrokan (*anti-collision*).
* **Stream Key Fleksibel**: Mendukung **Stream Key unik yang berbeda untuk setiap video/sesi**.
* **Telegram Alert**: Mengirimkan notifikasi langsung ke akun **Telegram** Anda saat siaran dimulai, selesai, atau terjadi gangguan.
* **Modern Web Dashboard**: Dilengkapi antarmuka web interaktif dengan tema *dark glassmorphism*.

---

## 🌟 Fitur Utama

- 🔑 **Stream Key Unik per Sesi**: Setiap jadwal sesi memiliki kolom Stream Key masing-masing sehingga Anda bebas menyiarkan video berbeda ke jadwal siaran YouTube Studio yang berbeda tanpa bentrok.
- 🐧 **Dukungan Penuh Windows & Linux**: Dapat dijalankan di PC Windows maupun server VPS Linux (Ubuntu, Debian, dll.) tanpa modifikasi kode.
- 🔲 **System Tray Icon (Windows)**: Dilengkapi dengan ikon tray di taskbar pojok kanan bawah Windows. Server dapat berjalan 100% senyap di latar belakang tanpa jendela CMD yang mengganggu layar.
- 📌 **Pinnable Shortcut ke Taskbar & Start Menu**: Dilengkapi skrip pembuat shortcut Windows resmi berikon custom (`icon.ico`) yang siap disematkan (*pin*) ke Taskbar atau Start Menu.
- 📱 **Notifikasi Telegram Otomatis**:
  - 🔴 **Live Dimulai**: Nama sesi, nama file video, mode streaming, jam mulai, estimasi waktu berakhir, dan durasi video.
  - ✅ **Live Selesai**: Nama sesi, total durasi siaran berjalan (*Jam-Menit-Detik*), dan status selesai sukses normal.
  - ⚠️ **Peringatan / Disconnect**: Detail peringatan jika koneksi internet terputus atau FFmpeg berhenti tak terduga.
- ⏱️ **3 Mode Durasi & Looping Fleksibel**:
  - **Mode A (Putar Sekali / Selesai Alami)**: Video diputar 1 kali apa adanya sampai selesai tanpa looping.
  - **Mode B (Looping Hingga Batas Durasi)**: Video berulang terus secara otomatis (`-stream_loop -1`) hingga target durasi tercapai (contoh: `03:00:00`).
  - **Mode C (Batas Durasi Tanpa Loop)**: Video dipotong tepat pada durasi yang ditentukan tanpa pengulangan.
- 📂 **Dual-Pane File Explorer Web**: Memilih file video PC/Server langsung dari antarmuka web yang intuitif dengan breadcrumb interaktif, filter pencarian live, dan pintasan cepat folder (Videos, Downloads, Documents, Drives Windows, serta direktori Root/Home Linux).
- 💾 **Backup & Restore Jadwal Sesi (JSON)**: Ekspor dan impor seluruh daftar jadwal sesi ke berkas `.json` untuk menyimpan dan berganti-ganti profil jadwal siaran (misal: *Jadwal_Weekday.json*, *Jadwal_Weekend.json*) dalam 1 klik.
- ⏳ **Live Countdown Timer**: Menghitung mundur waktu secara real-time menuju sesi siaran terdekat berikutnya.
- 📊 **Real-time Telemetri & Log**: Memantau Bitrate, FPS, Kecepatan Encoding, Processed Time, dan output terminal FFmpeg secara langsung dari browser.
- 🕹️ **Kontrol Manual On-Demand**: Tombol **"Putar & Live Sekarang"** untuk memulai siaran secara instan dan **"Hentikan Live"** untuk graceful stop.

---

## 🛠️ Arsitektur & Teknologi

* **Backend**: Python 3.10+, FastAPI, Uvicorn, Pydantic v2, Jinja2
* **Streaming Engine**: FFmpeg & FFprobe (Subprocess streaming H.264 / AAC FLV to RTMP)
* **Scheduler**: Multi-threaded Precision Background Timer
* **OS & Tray Integration**: `pystray`, `Pillow`, Windows Win32 API (`ctypes`) dengan auto-fallback headless Linux
* **Frontend**: HTML5, Vanilla CSS (Modern Dark Glassmorphism), Vanilla JavaScript ES6+, FontAwesome 6

---

## 🚀 Cara Instalasi & Menjalankan

### 1. Prasyarat Sistem
Pastikan sistem Anda telah terpasang:
1. **Python 3.10+** (Centang *"Add Python to PATH"* saat instalasi di Windows).
2. **FFmpeg** terpasang dan dapat diakses dari terminal/CMD (`ffmpeg -version`).

### 2. Clone Repository
```bash
git clone https://github.com/maxnmrantau/StreamYT-Pro.git
cd StreamYT-Pro
```

### 3. Install Dependensi
```bash
pip install -r requirements.txt
```

### 4. Menjalankan di Windows

Tersedia **2 opsi peluncuran**:

#### 🌟 Opsi A: Menjalankan Tanpa Jendela CMD (Rekomendasi)
Double-click file **`Jalankan_Tanpa_CMD.vbs`** (atau `run_hidden.vbs`):
* Server berjalan 100% di latar belakang tanpa jendela CMD hitam di layar.
* Ikon aplikasi aktif di **System Tray (Pojok Kanan Bawah Windows)**.
* Browser web akan otomatis terbuka ke `http://localhost:8000`.

#### 💻 Opsi B: Menjalankan dengan Jendela CMD
Double-click file **`run.bat`** (atau jalankan `python app.py` di terminal).

---

## 🐧 Panduan Penggunaan di Linux / VPS Server

### 1. Install Python & FFmpeg (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv ffmpeg -y
```

### 2. Jalankan dengan Script `run.sh`
```bash
chmod +x run.sh
./run.sh
```

### 3. Menjalankan 24/7 di Background VPS (Systemd Service)
Buat file service di `/etc/systemd/system/streamyt.service`:
```ini
[Unit]
Description=StreamYT Pro Server
After=network.target

[Service]
User=root
WorkingDirectory=/var/www/StreamYT-Pro
ExecStart=/usr/bin/python3 app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```
Kemudian aktifkan service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable streamyt
sudo systemctl start streamyt
```
Dashboard dapat diakses melalui browser di `http://IP_VPS_ANDA:8000`.

---

## 📖 Panduan Penggunaan

1. **Buka Dashboard**: Akses **`http://localhost:8000`** (atau IP VPS Anda) di browser.
2. **Tambah Jadwal Sesi**:
   * Klik tombol **`+ Tambah Jadwal Sesi`**.
   * Masukkan **Nama Sesi**.
   * Klik **`Pilih File Video`** untuk memilih berkas video dari komputer/server Anda.
   * Masukkan **YouTube Stream Key** khusus untuk jadwal video tersebut dari YouTube Studio.
   * Atur **Jam Mulai** (format 24 jam, misal `08:00`) dan **Hari Aktif** (Senin–Minggu).
   * Pilih **Mode Durasi & Looping** (Mode A, B, atau C).
   * Klik **Simpan Sesi**.
3. **Selesai!** Server akan otomatis menghitung mundur dan memulai streaming ke YouTube Live tepat pada jam yang ditentukan.

---

## ⏱️ Penjelasan Mode Durasi (A, B, C)

| Mode | Nama Mode | Cara Kerja | Contoh Penggunaan |
| :--- | :--- | :--- | :--- |
| **Mode A** | **Sesuai Panjang Video** | Video diputar 1 kali dari awal hingga selesai apa adanya tanpa durasi/looping. | Video webinar / rekaman pengajian 1 jam 45 menit. |
| **Mode B** | **Loop Video Sampai Durasi** | Video berulang (*loop*) terus menerus secara otomatis hingga batas durasi tercapai. | Video musik relaksasi 10 menit di-looping selama 3 jam (`03:00:00`). |
| **Mode C** | **Batas Durasi (Tanpa Loop)** | Video dipotong tepat pada durasi yang ditentukan tanpa pengulangan. | Video rekaman 4 jam yang hanya ingin disiarkan selama 2 jam pertama. |

---

## 📱 Panduan Notifikasi Telegram

StreamYT Pro dapat mengirimkan laporan siaran langsung ke HP/akun Telegram Anda.

1. Buka Telegram dan cari **`@BotFather`** > kirim pesan `/newbot` > ikuti petunjuk untuk mendapatkan **Bot Token**.
2. Buka bot yang baru dibuat di Telegram dan klik tombol **`/start`**.
3. Cari **`@userinfobot`** di Telegram untuk melihat **Chat ID** akun Anda (berupa angka, contoh: `370344988`).
4. Pada dashboard StreamYT Pro, klik **Pengaturan** > pilih tab **Notifikasi Telegram**:
   * Aktifkan toggle switch **"Aktifkan Notifikasi Telegram"**.
   * Masukkan **Bot Token** dan **Chat ID**.
   * Klik tombol **"Kirim Pesan Uji Coba (Test)"** untuk memastikan bot terhubung.
   * Klik **Simpan Pengaturan**.

---

## 🔲 System Tray & Shortcut Taskbar (Windows)

### 1. Menu System Tray (Pojok Kanan Bawah Windows)
Klik kanan pada ikon tray StreamYT Pro:
* 🌐 **`Buka Dashboard Web`**: Membuka browser ke dashboard.
* 👁️ **`Tampilkan / Sembunyikan CMD`**: Memunculkan atau menyembunyikan jendela terminal kapan saja.
* ❌ **`Keluar & Tutup Server`**: Menghentikan siaran aktif dan mematikan server dengan aman.

### 2. Membuat Shortcut yang Bisa di-Pin ke Taskbar / Start Menu
Cukup double-click file **`Buat_Shortcut_Pinnable.vbs`**:
* File shortcut **`StreamYT Pro`** berikon resmi akan otomatis dibuat di **Desktop**.
* Anda dapat langsung **klik kanan > Pin to taskbar** atau **Pin to Start**!

---

## 📁 Struktur Berkas Proyek

```text
StreamYT-Pro/
├── app.py                      # FastAPI server & route handlers
├── run.sh                      # Launcher script untuk Linux / VPS
├── Jalankan_Tanpa_CMD.vbs      # Silent launcher Windows (tanpa jendela CMD)
├── run_hidden.vbs              # Silent launcher backup
├── run.bat                     # Windows batch launcher
├── Buat_Shortcut_Pinnable.vbs  # Generator shortcut resmi Taskbar / Start Menu
├── requirements.txt            # Dependensi Python
├── icon.png                    # Ikon aplikasi asli
├── app_icon.ico                # Ikon Windows multi-resolusi (16px - 256px)
├── core/
│   ├── __init__.py
│   ├── config.py               # Penyimpanan config & video metadata inspector
│   ├── stream_engine.py        # FFmpeg process engine & live telemetry
│   ├── scheduler.py            # Precision local time scheduler loop
│   └── tray_manager.py         # System Tray & window visibility manager (Cross-Platform)
├── data/
│   ├── config.example.json     # Template konfigurasi contoh
│   └── sessions.example.json   # Template jadwal sesi contoh
├── static/
│   ├── css/dashboard.css       # Dark glassmorphism styling
│   └── js/dashboard.js         # Interaktivitas UI, polling & CRUD
├── templates/
│   └── index.html              # Dashboard Web Template
├── LICENSE                     # Lisensi MIT
└── README.md                   # Dokumentasi resmi
```

---

## 🛡️ Keamanan & Privasi

* **100% Lokal**: Seluruh data jadwal sesi, file video, dan token Telegram disimpan secara lokal di hard drive Anda (`data/config.json` dan `data/sessions.json`).
* **Kredensial Tidak Diunggah**: Berkas sensitif dimasukkan ke `.gitignore` sehingga aman dari kebocoran ke publik saat melakukan git commit.

---

## 📄 Lisensi

Proyek ini dilisensikan di bawah lisensi **[MIT License](LICENSE)** — bebas digunakan, dimodifikasi, dan didistribusikan untuk keperluan pribadi maupun komersial.

---

<div align="center">

Dibuat dengan ❤️ oleh [maxnmrantau](https://github.com/maxnmrantau)

</div>
