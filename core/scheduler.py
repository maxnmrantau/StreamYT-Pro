import time
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple

from core.config import SessionManager, ConfigManager, add_log
from core.stream_engine import stream_engine


class BackgroundScheduler:
    def __init__(self):
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._last_triggered: Dict[str, str] = {}  # {session_id: "YYYY-MM-DD HH:MM"}
        self._lock = threading.Lock()

    def start(self):
        with self._lock:
            if self._running:
                return
            self._running = True
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()
            add_log("INFO", "Background Scheduler aktif dan siap memantau jadwal.", "SCHEDULER")

    def stop(self):
        with self._lock:
            self._running = False
            add_log("INFO", "Background Scheduler dihentikan.", "SCHEDULER")

    def is_running(self) -> bool:
        with self._lock:
            return self._running

    def _loop(self):
        while self._running:
            try:
                self._check_and_trigger()
            except Exception as e:
                add_log("ERROR", f"Error pada scheduler loop: {e}", "SCHEDULER")
            
            # Cek setiap 2-3 detik
            time.sleep(2)

    def _check_and_trigger(self):
        now = datetime.now()
        current_time_str = now.strftime("%H:%M")
        current_date_str = now.strftime("%Y-%m-%d")
        current_weekday = now.weekday()  # 0: Senin, 6: Minggu

        # Jika sedang live streaming, jangan mulai sesi baru
        if stream_engine.is_live():
            return

        sessions = SessionManager.get_sessions()
        for session in sessions:
            if not session.get("enabled", True):
                continue

            # Cek hari aktif
            days = session.get("days", [])
            if days and len(days) > 0 and current_weekday not in days:
                continue

            raw_time = session.get("start_time", "").strip()
            session_id = session.get("id")

            # Normalisasi format jam ke HH:MM (contoh: '8:0' atau '08:00:00' -> '08:00')
            try:
                parts = list(map(int, raw_time.split(":")))
                if len(parts) >= 2:
                    session_time = f"{parts[0]:02d}:{parts[1]:02d}"
                else:
                    session_time = raw_time
            except Exception:
                session_time = raw_time

            # Cek apakah jam dan menit sekarang cocok
            if session_time == current_time_str:
                trigger_key = f"{session_id}_{current_date_str}_{current_time_str}"
                if self._last_triggered.get(session_id) == trigger_key:
                    continue  # Sudah dipicu pada menit ini

                # Catat agar tidak double trigger
                self._last_triggered[session_id] = trigger_key
                add_log("INFO", f"Waktu jadwal tercapai untuk sesi '{session.get('name')}' ({session_time}). Menjalankan live...", "SCHEDULER")
                
                success, msg = stream_engine.start_stream(session)
                if not success:
                    add_log("ERROR", f"Scheduler gagal memulai sesi '{session.get('name')}': {msg}", "SCHEDULER")
                break

    def get_next_session_info(self) -> Optional[Dict[str, Any]]:
        """Mencari sesi aktif berikutnya beserta waktu mundur (countdown)."""
        now = datetime.now()
        sessions = SessionManager.get_sessions()
        active_sessions = [s for s in sessions if s.get("enabled", True)]
        
        if not active_sessions:
            return None

        candidates = []
        # Cek kemungkinan trigger dalam rentang 7 hari ke depan
        for day_offset in range(8):
            check_date = now.date() + timedelta(days=day_offset)
            weekday = check_date.weekday()

            for s in active_sessions:
                days = s.get("days", [])
                if days and len(days) > 0 and weekday not in days:
                    continue

                try:
                    raw_st = s.get("start_time", "00:00").strip()
                    parts = list(map(int, raw_st.split(":")))
                    if len(parts) < 2:
                        continue
                    h, m = parts[0], parts[1]
                    session_dt = datetime(check_date.year, check_date.month, check_date.day, h, m, 0)
                    
                    if session_dt > now:
                        diff_sec = int((session_dt - now).total_seconds())
                        candidates.append({
                            "session": s,
                            "target_dt": session_dt.strftime("%Y-%m-%d %H:%M:%S"),
                            "seconds_remaining": diff_sec,
                            "day_name": ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"][weekday],
                            "is_today": (day_offset == 0)
                        })
                except Exception:
                    continue

        if not candidates:
            return None

        candidates.sort(key=lambda x: x["seconds_remaining"])
        return candidates[0]


# Global singleton instance
scheduler = BackgroundScheduler()
