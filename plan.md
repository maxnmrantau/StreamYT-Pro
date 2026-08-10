# Plan: PC Streaming Server Terjadwal untuk YouTube

## Ringkasan
Aplikasi **web dashboard lokal** yang berjalan di PC, berfungsi menjadwalkan
beberapa sesi live streaming ke YouTube dalam sehari (contoh: pagi, siang,
sore). Tiap sesi punya video, jam mulai, dan durasi (opsional) sendiri.
Bukan continuous 24 jam — tiap sesi jadi broadcast/video terpisah di YouTube,
tapi tetap pakai **1 stream key statis** yang sama.

## Keputusan Desain
- **Mode streaming**: sesi terpisah (bukan continuous nonstop)
- **Interface**: web dashboard lokal (Flask/FastAPI + halaman sederhana),
  dijalankan sebagai service/background process di PC — bukan aplikasi GUI
  yang harus dibuka terus
- **Stream key**: satu key statis, disimpan di config, dipakai berulang untuk
  semua sesi (aman menurut dokumentasi YouTube — satu stream bisa dipakai
  untuk banyak broadcast di waktu berbeda)

---

## Cara Kerja Scheduler

1. Kamu daftarkan sesi lewat dashboard: pilih video, jam mulai, durasi (opsional)
2. Background service cek waktu berjalan (loop tiap beberapa detik)
3. Saat jam sesi tercapai → jalankan ffmpeg ke RTMP YouTube dengan stream key statis
4. Saat sesi selesai (lihat logika durasi di bawah) → matikan proses ffmpeg
5. Tunggu sampai sesi berikutnya, ulangi

## Logika Durasi (penting)

### Mode A — Tanpa durasi (durasi kosong)
Video diputar apa adanya, **tidak looping**. Begitu video habis, ffmpeg
otomatis berhenti sendiri.
```bash
ffmpeg -re -i video.mp4 -c:v libx264 -preset veryfast -c:a aac \
  -f flv rtmp://a.rtmp.youtube.com/live2/STREAM_KEY
```
Contoh: video 2 jam 11 menit tanpa durasi diisi → live berjalan persis 2 jam
11 menit lalu berhenti otomatis.

### Mode B — Dengan durasi diisi (looping sampai durasi tercapai)
Video di-loop otomatis, dipotong paksa saat durasi tercapai (bisa terpotong
di tengah video pada putaran terakhir).
```bash
ffmpeg -re -stream_loop -1 -i video.mp4 -t 03:00:00 \
  -c:v libx264 -preset veryfast -c:a aac \
  -f flv rtmp://a.rtmp.youtube.com/live2/STREAM_KEY
```
Contoh: video 2 jam 11 menit, durasi di-set 3 jam → video muter ulang dari
awal setelah 2 jam 11 menit, lalu dipotong paksa di menit ke-49 putaran kedua.

### Mode C — Durasi lebih pendek dari video
Sama seperti Mode A tapi dipotong paksa sebelum video natural selesai
(pakai `-t` tanpa `-stream_loop`).

**Di dashboard, ini cukup jadi 1 field opsional "Durasi (kosongkan jika ikut
durasi video)".**

---

## Fitur

### Fase 1 — MVP
- [ ] Form tambah sesi: pilih file video, jam mulai, durasi (opsional)
- [ ] Daftar sesi terjadwal (tabel: video, jam, durasi, status)
- [ ] Background scheduler yang menjalankan/mematikan ffmpeg sesuai jadwal
- [ ] Logika durasi: Mode A (tanpa loop) dan Mode B/C (loop + potong paksa)
- [ ] Config stream key statis (input sekali, tersimpan)
- [ ] Status live saat ini (sedang live / menunggu jadwal / idle) di dashboard
- [ ] Log dasar (kapan mulai, kapan berhenti, error ffmpeg jika ada)

### Fase 2 — Penyempurnaan (opsional, belakangan)
- [ ] Validasi file video sebelum dijadwalkan (cek file rusak/codec aneh)
- [ ] Restart otomatis kalau ffmpeg tiba-tiba crash saat sesi berjalan
- [ ] Riwayat sesi yang sudah dijalankan

### Sengaja TIDAK dibangun (di luar scope)
- Continuous seamless streaming (named pipe/concat dinamis)
- Integrasi YouTube Data API (auto-create broadcast)
- Watchdog kompleks, auto-reconnect canggih
- Multi-output, overlay/watermark, notifikasi webhook, statistik lanjutan

---

## Tech Stack
- **Backend**: Python (FastAPI atau Flask) — jalankan scheduler + serve dashboard
- **Scheduler**: loop sederhana (cek waktu tiap beberapa detik) atau library
  `APScheduler`
- **Streaming**: ffmpeg via subprocess
- **Penyimpanan jadwal**: JSON atau SQLite ringan (tidak perlu database berat)
- **Frontend**: HTML sederhana (form + tabel), tidak perlu framework JS berat

---

## Struktur Proyek (usulan)
```
pc-streaming-server/
├── app.py                 # entry point FastAPI/Flask
├── core/
│   ├── scheduler.py       # loop pengecekan jadwal
│   ├── stream_engine.py   # wrapper ffmpeg (Mode A/B/C)
│   └── config.py          # baca/simpan stream key & sesi
├── templates/
│   └── dashboard.html     # form tambah sesi + tabel jadwal
├── static/
│   └── style.css
└── data/
    ├── sessions.json      # daftar sesi terjadwal
    └── stream.log         # log aktivitas
```

---

## Langkah Selanjutnya
1. Konfirmasi PC akan selalu menyala di jam-jam jadwal (pagi/siang/sore) —
   scheduler tidak bisa jalan kalau PC mati/sleep
2. Bangun prototipe `stream_engine.py` dulu (Mode A dan B), tes manual dengan
   1 video sebelum masuk ke scheduler
3. Setelah stream engine teruji, baru bangun scheduler + dashboard di atasnya
