import os
import json
import uuid
import subprocess
import shutil
from datetime import datetime
from typing import List, Dict, Optional, Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
SESSIONS_FILE = os.path.join(DATA_DIR, "sessions.json")
LOG_FILE = os.path.join(DATA_DIR, "stream.log")

# Pastikan direktori data tersedia
os.makedirs(DATA_DIR, exist_ok=True)

DEFAULT_CONFIG = {
    "stream_key": "",
    "rtmp_url": "rtmp://a.rtmp.youtube.com/live2",
    "video_preset": "veryfast",
    "video_bitrate": "4500k",
    "audio_bitrate": "128k",
    "check_interval_seconds": 2,
    "telegram_enabled": False,
    "telegram_bot_token": "",
    "telegram_chat_id": "",
    "telegram_notify_start": True,
    "telegram_notify_end": True,
    "telegram_notify_error": True
}

_log_buffer: List[Dict[str, Any]] = []
MAX_BUFFER_LOGS = 200


def add_log(level: str, message: str, source: str = "SYSTEM"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = {
        "timestamp": timestamp,
        "level": level.upper(),
        "source": source,
        "message": message
    }
    _log_buffer.append(entry)
    if len(_log_buffer) > MAX_BUFFER_LOGS:
        _log_buffer.pop(0)

    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] [{entry['level']}] [{source}] {message}\n")
    except Exception as e:
        print(f"Failed to write log: {e}")


def get_recent_logs(limit: int = 100) -> List[Dict[str, Any]]:
    return _log_buffer[-limit:]


def send_telegram_notification(text: str, event_type: str = "general") -> None:
    """Mengirim notifikasi Telegram secara asynchronous/background."""
    import threading
    import urllib.request
    import urllib.parse

    cfg = ConfigManager.get_config()
    if not cfg.get("telegram_enabled"):
        return

    # Cek filter event
    if event_type == "start" and not cfg.get("telegram_notify_start", True):
        return
    if event_type == "end" and not cfg.get("telegram_notify_end", True):
        return
    if event_type == "error" and not cfg.get("telegram_notify_error", True):
        return

    bot_token = cfg.get("telegram_bot_token", "").strip()
    chat_id = cfg.get("telegram_chat_id", "").strip()

    if not bot_token or not chat_id:
        return

    def _send_worker():
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    add_log("DEBUG", "Notifikasi Telegram berhasil dikirim", "TELEGRAM")
                else:
                    add_log("WARN", f"Telegram API response: {response.status}", "TELEGRAM")
        except Exception as e:
            add_log("ERROR", f"Gagal mengirim notifikasi Telegram: {e}", "TELEGRAM")

    threading.Thread(target=_send_worker, daemon=True).start()


class ConfigManager:
    @staticmethod
    def get_config() -> Dict[str, Any]:
        if not os.path.exists(CONFIG_FILE):
            ConfigManager.save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG.copy()
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                merged = DEFAULT_CONFIG.copy()
                merged.update(data)
                return merged
        except Exception as e:
            add_log("ERROR", f"Error reading config: {e}", "CONFIG")
            return DEFAULT_CONFIG.copy()

    @staticmethod
    def save_config(config_data: Dict[str, Any]) -> bool:
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            add_log("ERROR", f"Error saving config: {e}", "CONFIG")
            return False

    @staticmethod
    def update_config(updates: Dict[str, Any]) -> Dict[str, Any]:
        cfg = ConfigManager.get_config()
        cfg.update(updates)
        ConfigManager.save_config(cfg)
        add_log("INFO", "Konfigurasi diperbarui", "CONFIG")
        return cfg


class SessionManager:
    @staticmethod
    def get_sessions() -> List[Dict[str, Any]]:
        if not os.path.exists(SESSIONS_FILE):
            SessionManager.save_sessions([])
            return []
        try:
            with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            add_log("ERROR", f"Error reading sessions: {e}", "SESSIONS")
            return []

    @staticmethod
    def save_sessions(sessions: List[Dict[str, Any]]) -> bool:
        try:
            with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
                json.dump(sessions, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            add_log("ERROR", f"Error saving sessions: {e}", "SESSIONS")
            return False

    @staticmethod
    def add_session(session_data: Dict[str, Any]) -> Dict[str, Any]:
        sessions = SessionManager.get_sessions()
        session_id = str(uuid.uuid4())[:8]
        new_session = {
            "id": session_id,
            "name": session_data.get("name", "Sesi Baru"),
            "video_path": session_data.get("video_path", "").strip(),
            "stream_key": session_data.get("stream_key", "").strip(),
            "start_time": session_data.get("start_time", "08:00"),  # HH:MM format
            "days": session_data.get("days", []),  # [] = everyday, [0,1,2,3,4,5,6]
            "duration": session_data.get("duration") or None,  # "HH:MM:SS" or None
            "loop": bool(session_data.get("loop", True)),
            "enabled": bool(session_data.get("enabled", True)),
            "created_at": datetime.now().isoformat()
        }
        sessions.append(new_session)
        SessionManager.save_sessions(sessions)
        add_log("INFO", f"Sesi '{new_session['name']}' ({new_session['start_time']}) ditambahkan.", "SESSIONS")
        return new_session

    @staticmethod
    def update_session(session_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        sessions = SessionManager.get_sessions()
        for idx, s in enumerate(sessions):
            if s["id"] == session_id:
                for k, v in updates.items():
                    if k == "stream_key":
                        # Hanya update jika bukan placeholder bintang
                        if v is not None and "*" not in str(v):
                            s["stream_key"] = str(v).strip()
                    elif k != "id":
                        s[k] = v
                sessions[idx] = s
                SessionManager.save_sessions(sessions)
                add_log("INFO", f"Sesi '{s['name']}' diperbarui.", "SESSIONS")
                return s
        return None

    @staticmethod
    def delete_session(session_id: str) -> bool:
        sessions = SessionManager.get_sessions()
        initial_len = len(sessions)
        sessions = [s for s in sessions if s["id"] != session_id]
        if len(sessions) < initial_len:
            SessionManager.save_sessions(sessions)
            add_log("INFO", f"Sesi {session_id} dihapus.", "SESSIONS")
            return True
        return False

    @staticmethod
    def toggle_session(session_id: str) -> Optional[bool]:
        sessions = SessionManager.get_sessions()
        for s in sessions:
            if s["id"] == session_id:
                s["enabled"] = not s.get("enabled", True)
                SessionManager.save_sessions(sessions)
                status_str = "diaktifkan" if s["enabled"] else "dinonaktifkan"
                add_log("INFO", f"Sesi '{s['name']}' {status_str}.", "SESSIONS")
                return s["enabled"]
        return None

    @staticmethod
    def get_session_by_id(session_id: str) -> Optional[Dict[str, Any]]:
        sessions = SessionManager.get_sessions()
        for s in sessions:
            if s["id"] == session_id:
                return s
        return None


def get_video_info(video_path: str) -> Dict[str, Any]:
    """Mengambil metadata video menggunakan ffprobe."""
    if not os.path.exists(video_path):
        return {"valid": False, "error": "File tidak ditemukan di path yang diberikan."}

    ffprobe_cmd = shutil.which("ffprobe")
    if not ffprobe_cmd:
        # Coba cek apakah ffmpeg ada di direktori yang sama
        ffmpeg_cmd = shutil.which("ffmpeg")
        if ffmpeg_cmd:
            probe_name = "ffprobe.exe" if sys.platform == "win32" else "ffprobe"
            probe_candidate = os.path.join(os.path.dirname(ffmpeg_cmd), probe_name)
            if os.path.exists(probe_candidate):
                ffprobe_cmd = probe_candidate

    if not ffprobe_cmd:
        file_size_mb = round(os.path.getsize(video_path) / (1024 * 1024), 2)
        return {
            "valid": True,
            "filename": os.path.basename(video_path),
            "size_mb": file_size_mb,
            "duration_str": "Unknown (ffprobe not found)",
            "duration_sec": 0
        }

    try:
        cmd = [
            ffprobe_cmd,
            "-v", "error",
            "-show_entries", "format=duration,size,bit_rate:stream=width,height,codec_name,codec_type",
            "-of", "json",
            video_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
        data = json.loads(result.stdout)
        
        format_info = data.get("format", {})
        duration_sec = float(format_info.get("duration", 0))
        size_bytes = int(format_info.get("size", os.path.getsize(video_path)))
        
        hours = int(duration_sec // 3600)
        minutes = int((duration_sec % 3600) // 60)
        seconds = int(duration_sec % 60)
        duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        # cari video stream info
        v_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
        width = v_stream.get("width")
        height = v_stream.get("height")
        v_codec = v_stream.get("codec_name")

        return {
            "valid": True,
            "filename": os.path.basename(video_path),
            "duration_sec": duration_sec,
            "duration_str": duration_str,
            "size_mb": round(size_bytes / (1024 * 1024), 2),
            "resolution": f"{width}x{height}" if width and height else "Unknown",
            "codec": v_codec or "Unknown"
        }
    except Exception as e:
        return {
            "valid": True,
            "filename": os.path.basename(video_path),
            "size_mb": round(os.path.getsize(video_path) / (1024 * 1024), 2),
            "duration_str": "Error reading metadata",
            "duration_sec": 0,
            "error": str(e)
        }
