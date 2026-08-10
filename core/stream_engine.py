import os
import re
import time
import shutil
import threading
import subprocess
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple

from core.config import ConfigManager, add_log, send_telegram_notification, get_video_info


class StreamEngine:
    def __init__(self):
        self._process: Optional[subprocess.Popen] = None
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        self.state = "IDLE"  # "IDLE", "STARTING", "LIVE", "STOPPING", "ERROR"
        self.active_session: Optional[Dict[str, Any]] = None
        self.start_time: Optional[float] = None
        self.last_error: Optional[str] = None
        
        # Realtime stats parsed from FFmpeg output
        self.stats = {
            "fps": "0",
            "bitrate": "0 kbits/s",
            "speed": "0x",
            "current_time": "00:00:00.00",
            "frame": "0",
            "drop": "0"
        }

    def is_live(self) -> bool:
        with self._lock:
            return self._process is not None and self._process.poll() is None

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            is_active = self._process is not None and self._process.poll() is None
            uptime = int(time.time() - self.start_time) if (is_active and self.start_time) else 0
            
            hours = uptime // 3600
            minutes = (uptime % 3600) // 60
            seconds = uptime % 60
            uptime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

            current_state = self.state
            if is_active and current_state != "LIVE" and uptime > 2:
                current_state = "LIVE"
                self.state = "LIVE"
            elif not is_active and current_state not in ["IDLE", "ERROR"]:
                current_state = "IDLE"
                self.state = "IDLE"

            return {
                "is_live": is_active,
                "state": current_state,
                "active_session": self.active_session,
                "uptime_seconds": uptime,
                "uptime_formatted": uptime_str,
                "stats": self.stats.copy(),
                "last_error": self.last_error
            }

    def build_ffmpeg_command(self, session: Dict[str, Any], config: Dict[str, Any]) -> Tuple[list, str]:
        ffmpeg_bin = shutil.which("ffmpeg") or "ffmpeg"
        video_path = session.get("video_path", "").strip()
        session_key = session.get("stream_key", "").strip()
        global_key = config.get("stream_key", "").strip()
        stream_key = session_key or global_key
        rtmp_url = config.get("rtmp_url", "rtmp://a.rtmp.youtube.com/live2").rstrip("/")
        
        if not stream_key:
            raise ValueError(f"Stream Key YouTube belum diisi untuk sesi '{session.get('name')}'. Silakan edit sesi dan masukkan Stream Key dari YouTube Studio.")
        
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"File video '{video_path}' tidak ditemukan.")

        target_rtmp = f"{rtmp_url}/{stream_key}"
        duration = session.get("duration")
        should_loop = session.get("loop", True)

        cmd = [ffmpeg_bin, "-re"]

        # Logika Mode A / B / C
        mode_desc = "Mode A (Tanpa Durasi - Putar Sekali Sampai Selesai)"
        if duration and duration.strip():
            if should_loop:
                # Mode B: Looping sampai durasi tercapai
                cmd.extend(["-stream_loop", "-1"])
                cmd.extend(["-i", video_path])
                cmd.extend(["-t", duration.strip()])
                mode_desc = f"Mode B (Looping hingga durasi {duration})"
            else:
                # Mode C: Durasi dipotong tanpa loop
                cmd.extend(["-i", video_path])
                cmd.extend(["-t", duration.strip()])
                mode_desc = f"Mode C (Durasi dibatasi {duration} tanpa loop)"
        else:
            # Mode A: Putar apa adanya tanpa loop
            cmd.extend(["-i", video_path])

        # Video & Audio Encoding Parameters
        preset = config.get("video_preset", "veryfast")
        v_bitrate = config.get("video_bitrate", "4500k")
        a_bitrate = config.get("audio_bitrate", "128k")

        cmd.extend([
            "-c:v", "libx264",
            "-preset", preset,
            "-b:v", v_bitrate,
            "-maxrate", v_bitrate,
            "-bufsize", "9000k",
            "-pix_fmt", "yuv420p",
            "-g", "60",
            "-c:a", "aac",
            "-b:a", a_bitrate,
            "-ar", "44100",
            "-f", "flv",
            target_rtmp
        ])

        return cmd, mode_desc

    def start_stream(self, session: Dict[str, Any]) -> Tuple[bool, str]:
        with self._lock:
            if self._process is not None and self._process.poll() is None:
                return False, "Streaming sudah sedang berjalan."

            config = ConfigManager.get_config()
            try:
                cmd, mode_desc = self.build_ffmpeg_command(session, config)
            except Exception as e:
                self.last_error = str(e)
                self.state = "ERROR"
                add_log("ERROR", f"Gagal mempersiapkan streaming: {e}", "STREAM")
                return False, str(e)

            self.state = "STARTING"
            self.active_session = session.copy()
            self.start_time = time.time()
            self.last_error = None
            self.stats = {
                "fps": "0",
                "bitrate": "0 kbits/s",
                "speed": "0x",
                "current_time": "00:00:00.00",
                "frame": "0",
                "drop": "0"
            }

            try:
                # Sembunyikan stream key pada log
                masked_cmd = [
                    arg if not arg.startswith("rtmp://") else f"{arg.rsplit('/', 1)[0]}/[STREAM_KEY_HIDDEN]"
                    for arg in cmd
                ]
                add_log("INFO", f"Memulai streaming sesi '{session.get('name')}' menggunakan {mode_desc}", "STREAM")
                add_log("DEBUG", f"FFmpeg command: {' '.join(masked_cmd)}", "STREAM")

                # Jalankan subprocess FFmpeg
                self._process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )

                # Jalankan background monitoring thread
                self._thread = threading.Thread(target=self._monitor_output, daemon=True)
                self._thread.start()

                # Hitung Durasi Video dan Estimasi Waktu Berakhir
                video_path = session.get("video_path", "")
                video_name = os.path.basename(video_path)
                v_meta = get_video_info(video_path)
                v_sec = float(v_meta.get("duration_sec", 0))

                v_h = int(v_sec // 3600)
                v_m = int((v_sec % 3600) // 60)
                v_s = int(v_sec % 60)
                durasi_video_str = f"{v_h} Jam {v_m} Menit {v_s} Detik"

                # Hitung target durasi live & estimasi jam berakhir
                now_dt = datetime.now()
                waktu_mulai_str = now_dt.strftime("%H:%M:%S WIB (%d/%m/%Y)")
                
                target_duration = session.get("duration")
                if target_duration and target_duration.strip():
                    try:
                        parts = list(map(int, target_duration.strip().split(":")))
                        if len(parts) == 3:
                            total_stream_sec = parts[0] * 3600 + parts[1] * 60 + parts[2]
                        elif len(parts) == 2:
                            total_stream_sec = parts[0] * 60 + parts[1]
                        else:
                            total_stream_sec = parts[0]
                    except Exception:
                        total_stream_sec = int(v_sec)
                else:
                    # Mode A: mengikuti durasi asli video
                    total_stream_sec = int(v_sec)

                if total_stream_sec > 0:
                    end_dt = now_dt + timedelta(seconds=total_stream_sec)
                    waktu_berakhir_str = end_dt.strftime("%H:%M:%S WIB (%d/%m/%Y)")
                else:
                    waktu_berakhir_str = "Selesai saat video berakhir"

                # Notifikasi Telegram saat Live Dimulai
                tg_msg = (
                    f"🔴 <b>YOUTUBE LIVE STREAMING DIMULAI</b>\n\n"
                    f"📌 <b>Nama Sesi:</b> {session.get('name')}\n"
                    f"🎬 <b>File Video:</b> <code>{video_name}</code>\n"
                    f"⚙️ <b>Mode:</b> {mode_desc}\n"
                    f"⏰ <b>Waktu Mulai:</b> {waktu_mulai_str}\n"
                    f"⏰ <b>Waktu Berakhir:</b> {waktu_berakhir_str}\n"
                    f"▶️ <b>Durasi Video:</b> {durasi_video_str}"
                )
                send_telegram_notification(tg_msg, event_type="start")

                return True, f"Streaming berhasil dimulai ({mode_desc})"
            except Exception as e:
                self.state = "ERROR"
                self.last_error = str(e)
                add_log("ERROR", f"Gagal menjalankan proses FFmpeg: {e}", "STREAM")
                
                # Notifikasi Telegram jika gagal start
                send_telegram_notification(
                    f"⚠️ <b>GAGAL MEMULAI LIVE YOUTUBE</b>\n\n"
                    f"📌 <b>Sesi:</b> {session.get('name')}\n"
                    f"❗ <b>Error:</b> {e}\n"
                    f"⏰ <b>Waktu:</b> {datetime.now().strftime('%H:%M:%S WIB')}",
                    event_type="error"
                )
                return False, str(e)

    def _monitor_output(self):
        """Thread background membaca output stderr dari FFmpeg."""
        proc = self._process
        if not proc or not proc.stderr:
            return

        fps_pattern = re.compile(r"fps=\s*([\d\.]+)")
        bitrate_pattern = re.compile(r"bitrate=\s*([\d\.]+kbits/s)")
        speed_pattern = re.compile(r"speed=\s*([\d\.]+x)")
        time_pattern = re.compile(r"time=\s*([\d\:\.]+)")
        frame_pattern = re.compile(r"frame=\s*(\d+)")
        drop_pattern = re.compile(r"drop=\s*(\d+)")

        try:
            for line in proc.stderr:
                line = line.strip()
                if not line:
                    continue

                # Parse status telemetry
                if "frame=" in line or "bitrate=" in line:
                    self.state = "LIVE"
                    fps_match = fps_pattern.search(line)
                    bitrate_match = bitrate_pattern.search(line)
                    speed_match = speed_pattern.search(line)
                    time_match = time_pattern.search(line)
                    frame_match = frame_pattern.search(line)
                    drop_match = drop_pattern.search(line)

                    if fps_match:
                        self.stats["fps"] = fps_match.group(1)
                    if bitrate_match:
                        self.stats["bitrate"] = bitrate_match.group(1)
                    if speed_match:
                        self.stats["speed"] = speed_match.group(1)
                    if time_match:
                        self.stats["current_time"] = time_match.group(1)
                    if frame_match:
                        self.stats["frame"] = frame_match.group(1)
                    if drop_match:
                        self.stats["drop"] = drop_match.group(1)
                else:
                    # Log peringatan atau error dari FFmpeg
                    if "error" in line.lower() or "failed" in line.lower() or "connection refused" in line.lower():
                        add_log("WARN", f"FFmpeg: {line}", "FFMPEG")
                    elif "opening" in line.lower() or "stream" in line.lower():
                        add_log("DEBUG", f"FFmpeg: {line}", "FFMPEG")

        except Exception as e:
            add_log("DEBUG", f"Stream monitor exited: {e}", "STREAM")
        finally:
            exit_code = proc.poll()
            if exit_code is None:
                exit_code = proc.wait()

            with self._lock:
                session_name = self.active_session.get("name") if self.active_session else "Unknown"
                video_name = os.path.basename(self.active_session.get("video_path", "")) if self.active_session else "-"
                
                uptime_sec = int(time.time() - self.start_time) if self.start_time else 0
                hrs = uptime_sec // 3600
                mins = (uptime_sec % 3600) // 60
                secs = uptime_sec % 60
                uptime_str = f"{hrs} Jam {mins} Menit {secs} Detik ({hrs:02d}:{mins:02d}:{secs:02d})"
                now_str = datetime.now().strftime("%H:%M:%S WIB (%d/%m/%Y)")

                if exit_code == 0:
                    add_log("INFO", f"Sesi live '{session_name}' selesai dengan sukses (exit code 0).", "STREAM")
                    self.state = "IDLE"
                    
                    # Notifikasi Telegram saat Selesai Sukses (Normal)
                    tg_msg = (
                        f"✅ <b>YOUTUBE LIVE STREAMING SELESAI</b>\n\n"
                        f"📌 <b>Nama Sesi:</b> {session_name}\n"
                        f"🎬 <b>File Video:</b> <code>{video_name}</code>\n"
                        f"⏱️ <b>Total Durasi Siaran:</b> {uptime_str}\n"
                        f"🏁 <b>Status:</b> Selesai Sukses (Normal)\n"
                        f"⏰ <b>Waktu Selesai:</b> {now_str}"
                    )
                    send_telegram_notification(tg_msg, event_type="end")
                else:
                    if self.state != "STOPPING":
                        msg = f"Sesi live '{session_name}' berhenti dengan kode {exit_code}."
                        add_log("WARN", msg, "STREAM")
                        self.last_error = msg
                        self.state = "IDLE"

                        # Notifikasi Telegram saat terjadi crash / diskoneksi tak terduga
                        tg_msg = (
                            f"⚠️ <b>YOUTUBE LIVE BERHENTI / DISCONNECT</b>\n\n"
                            f"📌 <b>Nama Sesi:</b> {session_name}\n"
                            f"🎬 <b>File Video:</b> <code>{video_name}</code>\n"
                            f"⏱️ <b>Total Durasi Berjalan:</b> {uptime_str}\n"
                            f"❗ <b>Keterangan:</b> FFmpeg exit dengan kode {exit_code}\n"
                            f"⏰ <b>Waktu:</b> {now_str}"
                        )
                        send_telegram_notification(tg_msg, event_type="error")
                    else:
                        add_log("INFO", f"Sesi live '{session_name}' dihentikan oleh pengguna.", "STREAM")
                        self.state = "IDLE"

                        # Notifikasi Telegram saat dihentikan manual oleh pengguna
                        tg_msg = (
                            f"🛑 <b>YOUTUBE LIVE DIHENTIKAN MANUAL</b>\n\n"
                            f"📌 <b>Nama Sesi:</b> {session_name}\n"
                            f"🎬 <b>File Video:</b> <code>{video_name}</code>\n"
                            f"⏱️ <b>Total Durasi Berjalan:</b> {uptime_str}\n"
                            f"🏁 <b>Status:</b> Dihentikan oleh Pengguna\n"
                            f"⏰ <b>Waktu:</b> {now_str}"
                        )
                        send_telegram_notification(tg_msg, event_type="end")

                self._process = None
                self.active_session = None

    def stop_stream(self) -> Tuple[bool, str]:
        with self._lock:
            if self._process is None or self._process.poll() is not None:
                self.state = "IDLE"
                self.active_session = None
                return True, "Tidak ada stream yang sedang berjalan."

            self.state = "STOPPING"
            add_log("INFO", "Menghentikan streaming...", "STREAM")

            try:
                # Coba kirim 'q' ke stdin untuk graceful shutdown
                if self._process.stdin:
                    try:
                        self._process.stdin.write("q\n")
                        self._process.stdin.flush()
                    except Exception:
                        pass

                # Berikan waktu 3 detik sebelum terminate
                try:
                    self._process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self._process.terminate()
                    try:
                        self._process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        self._process.kill()

                self._process = None
                self.active_session = None
                self.state = "IDLE"
                add_log("INFO", "Streaming berhasil dihentikan.", "STREAM")
                return True, "Streaming berhasil dihentikan."
            except Exception as e:
                self.state = "ERROR"
                self.last_error = str(e)
                add_log("ERROR", f"Gagal menghentikan streaming: {e}", "STREAM")
                return False, str(e)


# Global singleton instance
stream_engine = StreamEngine()
