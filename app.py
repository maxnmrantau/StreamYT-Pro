import os
import json
import uuid
import glob
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Request, HTTPException, Body
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from core.config import (
    BASE_DIR, ConfigManager, SessionManager,
    get_video_info, add_log, get_recent_logs
)
from core.stream_engine import stream_engine
from core.scheduler import scheduler
from core.tray_manager import tray_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start background scheduler & system tray
    add_log("INFO", "Server web dimulai.", "SYSTEM")
    scheduler.start()
    tray_manager.start_in_background()
    yield
    # Shutdown: Stop streaming and scheduler
    add_log("INFO", "Server web sedang dimatikan...", "SYSTEM")
    scheduler.stop()
    stream_engine.stop_stream()


app = FastAPI(title="PC YouTube Stream Server", lifespan=lifespan)

# Setup directories
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "css"), exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "js"), exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


# Pydantic models for request validation
class SessionCreateUpdate(BaseModel):
    name: str
    video_path: str
    stream_key: Optional[str] = ""
    start_time: str
    days: Optional[List[int]] = []
    duration: Optional[str] = None
    loop: Optional[bool] = True
    enabled: Optional[bool] = True


class ConfigUpdate(BaseModel):
    stream_key: Optional[str] = None
    rtmp_url: Optional[str] = None
    video_preset: Optional[str] = None
    video_bitrate: Optional[str] = None
    audio_bitrate: Optional[str] = None
    telegram_enabled: Optional[bool] = None
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    telegram_notify_start: Optional[bool] = None
    telegram_notify_end: Optional[bool] = None
    telegram_notify_error: Optional[bool] = None


class TelegramTestRequest(BaseModel):
    bot_token: Optional[str] = None
    chat_id: Optional[str] = None


class BrowseRequest(BaseModel):
    directory: Optional[str] = ""


class ValidateVideoRequest(BaseModel):
    video_path: str


# ==========================================
# Frontend Route
# ==========================================
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"now": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    )


# ==========================================
# API Routes: Status & Live Control
# ==========================================
@app.get("/api/status")
async def get_system_status():
    stream_status = stream_engine.get_status()
    next_session = scheduler.get_next_session_info()
    config = ConfigManager.get_config()
    has_key = bool(config.get("stream_key", "").strip())

    return {
        "status": "success",
        "current_time": datetime.now().strftime("%H:%M:%S"),
        "current_date": datetime.now().strftime("%A, %d %B %Y"),
        "stream": stream_status,
        "scheduler_running": scheduler.is_running(),
        "has_stream_key": has_key,
        "next_session": next_session
    }


@app.post("/api/stream/stop")
async def stop_live_stream():
    success, message = stream_engine.stop_stream()
    return {"status": "success" if success else "error", "message": message}


# ==========================================
# API Routes: Sessions Management
# ==========================================
@app.get("/api/sessions")
async def get_sessions():
    sessions = SessionManager.get_sessions()
    enhanced_sessions = []
    for s in sessions:
        item = s.copy()
        v_path = s.get("video_path", "")
        item["file_exists"] = os.path.exists(v_path)
        item["filename"] = os.path.basename(v_path) if v_path else ""
        
        # Mask stream key session
        raw_key = s.get("stream_key", "")
        item["has_stream_key"] = bool(raw_key)
        if raw_key:
            if len(raw_key) > 8:
                item["masked_stream_key"] = raw_key[:4] + "*" * (len(raw_key) - 8) + raw_key[-4:]
            else:
                item["masked_stream_key"] = "********"
        else:
            item["masked_stream_key"] = ""
            
        enhanced_sessions.append(item)
    return {"status": "success", "data": enhanced_sessions}


@app.post("/api/sessions")
async def create_session(session: SessionCreateUpdate):
    if not session.name.strip():
        raise HTTPException(status_code=400, detail="Nama sesi wajib diisi.")
    if not session.video_path.strip():
        raise HTTPException(status_code=400, detail="Path file video wajib diisi.")
    if not session.start_time.strip():
        raise HTTPException(status_code=400, detail="Jam mulai wajib diisi.")

    created = SessionManager.add_session(session.dict())
    return {"status": "success", "data": created}


@app.put("/api/sessions/{session_id}")
async def update_session(session_id: str, session: SessionCreateUpdate):
    updated = SessionManager.update_session(session_id, session.dict())
    if not updated:
        raise HTTPException(status_code=404, detail="Sesi tidak ditemukan.")
    return {"status": "success", "data": updated}


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    success = SessionManager.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Sesi tidak ditemukan.")
    return {"status": "success", "message": "Sesi berhasil dihapus."}


@app.post("/api/sessions/{session_id}/toggle")
async def toggle_session(session_id: str):
    result = SessionManager.toggle_session(session_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Sesi tidak ditemukan.")
    return {"status": "success", "enabled": result}


@app.post("/api/sessions/{session_id}/start")
async def start_session_manual(session_id: str):
    session = SessionManager.get_session_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sesi tidak ditemukan.")

    success, msg = stream_engine.start_stream(session)
    if not success:
        return JSONResponse(status_code=400, content={"status": "error", "message": msg})
    return {"status": "success", "message": msg}


@app.get("/api/sessions-export")
async def export_sessions():
    """Mengunduh berkas backup jadwal sesi dalam format JSON."""
    sessions = SessionManager.get_sessions()
    filename = f"streamyt_sessions_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    content = json.dumps(sessions, indent=2, ensure_ascii=False)
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.post("/api/sessions-import")
async def import_sessions(data: Dict[str, Any] = Body(...)):
    """Mengimpor jadwal sesi dari berkas JSON."""
    imported_list = data.get("sessions", [])
    mode = data.get("mode", "replace")  # 'replace' atau 'merge'

    if not isinstance(imported_list, list):
        raise HTTPException(status_code=400, detail="Format JSON sesi tidak valid (harus berupa array sesi).")

    # Validasi dan sanitasi item sesi
    valid_sessions = []
    for item in imported_list:
        if not isinstance(item, dict):
            continue
        valid_item = {
            "id": str(item.get("id") or uuid.uuid4())[:8],
            "name": str(item.get("name", "Sesi Impor")).strip(),
            "video_path": str(item.get("video_path", "")).strip(),
            "stream_key": str(item.get("stream_key", "")).strip(),
            "start_time": str(item.get("start_time", "08:00")).strip(),
            "days": item.get("days", []),
            "duration": item.get("duration") or None,
            "loop": bool(item.get("loop", True)),
            "enabled": bool(item.get("enabled", True)),
            "created_at": item.get("created_at") or datetime.now().isoformat()
        }
        valid_sessions.append(valid_item)

    if not valid_sessions:
        raise HTTPException(status_code=400, detail="Tidak ada data sesi yang valid di dalam file.")

    if mode == "merge":
        current = SessionManager.get_sessions()
        # Hindari ID duplikat
        existing_ids = {s["id"] for s in current}
        for s in valid_sessions:
            if s["id"] in existing_ids:
                s["id"] = str(uuid.uuid4())[:8]
            current.append(s)
        SessionManager.save_sessions(current)
        add_log("INFO", f"Berhasil menggabungkan {len(valid_sessions)} sesi impor.", "SESSIONS")
    else:
        # Mode Replace
        SessionManager.save_sessions(valid_sessions)
        add_log("INFO", f"Berhasil memuat {len(valid_sessions)} sesi impor (Replace).", "SESSIONS")

    return {"status": "success", "count": len(valid_sessions), "message": f"{len(valid_sessions)} sesi berhasil dimuat!"}


# ==========================================
# API Routes: System & Console Tray
# ==========================================
@app.post("/api/system/hide-console")
async def hide_console_window():
    """Menyembunyikan jendela terminal CMD ke system tray."""
    tray_manager.hide_console()
    return {"status": "success", "message": "Jendela server disembunyikan ke System Tray"}


@app.post("/api/system/show-console")
async def show_console_window():
    """Menampilkan kembali jendela terminal CMD."""
    tray_manager.show_console()
    return {"status": "success", "message": "Jendela server ditampilkan kembali"}


@app.get("/api/system/tray-info")
async def get_tray_info():
    return {
        "status": "success",
        "is_console_hidden": tray_manager._is_console_hidden,
        "has_icon": os.path.exists(os.path.join(BASE_DIR, "icon.png"))
    }


# ==========================================
# API Routes: Config & Settings
# ==========================================
@app.get("/api/config")
async def get_config():
    cfg = ConfigManager.get_config()
    raw_key = cfg.get("stream_key", "")
    masked_key = ""
    if raw_key:
        if len(raw_key) > 8:
            masked_key = raw_key[:4] + "*" * (len(raw_key) - 8) + raw_key[-4:]
        else:
            masked_key = "********"

    raw_tg_token = cfg.get("telegram_bot_token", "")
    masked_tg_token = ""
    if raw_tg_token:
        if len(raw_tg_token) > 10:
            masked_tg_token = raw_tg_token[:5] + "*" * (len(raw_tg_token) - 9) + raw_tg_token[-4:]
        else:
            masked_tg_token = "********"

    return {
        "status": "success",
        "data": {
            "has_key": bool(raw_key),
            "masked_key": masked_key,
            "rtmp_url": cfg.get("rtmp_url", "rtmp://a.rtmp.youtube.com/live2"),
            "video_preset": cfg.get("video_preset", "veryfast"),
            "video_bitrate": cfg.get("video_bitrate", "4500k"),
            "audio_bitrate": cfg.get("audio_bitrate", "128k"),
            "telegram_enabled": bool(cfg.get("telegram_enabled", False)),
            "has_tg_token": bool(raw_tg_token),
            "masked_tg_token": masked_tg_token,
            "telegram_chat_id": cfg.get("telegram_chat_id", ""),
            "telegram_notify_start": bool(cfg.get("telegram_notify_start", True)),
            "telegram_notify_end": bool(cfg.get("telegram_notify_end", True)),
            "telegram_notify_error": bool(cfg.get("telegram_notify_error", True))
        }
    }


@app.post("/api/config")
async def save_config(config_in: ConfigUpdate):
    cfg = ConfigManager.get_config()
    updates = {}
    
    # Stream key: hanya update jika diisi dan TIDAK mengandung karakter bintang '*'
    if config_in.stream_key is not None and config_in.stream_key.strip() != "":
        if "*" not in config_in.stream_key:
            updates["stream_key"] = config_in.stream_key.strip()
            
    if config_in.rtmp_url is not None:
        updates["rtmp_url"] = config_in.rtmp_url.strip()
    if config_in.video_preset is not None:
        updates["video_preset"] = config_in.video_preset.strip()
    if config_in.video_bitrate is not None:
        updates["video_bitrate"] = config_in.video_bitrate.strip()
    if config_in.audio_bitrate is not None:
        updates["audio_bitrate"] = config_in.audio_bitrate.strip()

    # Telegram settings
    if config_in.telegram_enabled is not None:
        updates["telegram_enabled"] = config_in.telegram_enabled
        
    # Telegram bot token: hanya update jika diisi dan TIDAK mengandung '*'
    if config_in.telegram_bot_token is not None and config_in.telegram_bot_token.strip() != "":
        if "*" not in config_in.telegram_bot_token:
            updates["telegram_bot_token"] = config_in.telegram_bot_token.strip()
            
    if config_in.telegram_chat_id is not None:
        updates["telegram_chat_id"] = config_in.telegram_chat_id.strip()
    if config_in.telegram_notify_start is not None:
        updates["telegram_notify_start"] = config_in.telegram_notify_start
    if config_in.telegram_notify_end is not None:
        updates["telegram_notify_end"] = config_in.telegram_notify_end
    if config_in.telegram_notify_error is not None:
        updates["telegram_notify_error"] = config_in.telegram_notify_error

    updated_cfg = ConfigManager.update_config(updates)
    return {"status": "success", "message": "Pengaturan berhasil disimpan."}


@app.post("/api/telegram/test")
async def test_telegram_notification(req: TelegramTestRequest):
    """Mengirim pesan uji coba ke Telegram."""
    import urllib.request
    import json

    cfg = ConfigManager.get_config()
    
    # Ambil token: jika mengandung '*' atau kosong, gunakan token asli dari config
    token = req.bot_token.strip() if req.bot_token else ""
    if not token or "*" in token:
        token = cfg.get("telegram_bot_token", "").strip()

    chat_id = req.chat_id.strip() if req.chat_id else cfg.get("telegram_chat_id", "").strip()

    if not token:
        raise HTTPException(status_code=400, detail="Bot Token Telegram belum diisi.")
    if not chat_id:
        raise HTTPException(status_code=400, detail="Chat ID Telegram belum diisi.")

    test_message = (
        "🤖 <b>StreamYT Pro - Tes Notifikasi Berhasil!</b>\n\n"
        "✅ Bot Telegram Anda telah berhasil terhubung dengan server siaran PC.\n"
        f"⏰ Waktu: <code>{datetime.now().strftime('%Y-%m-%d %H:%M:%S WIB')}</code>\n\n"
        "Siap menerima notifikasi otomatis saat live streaming dimulai, selesai, atau terjadi gangguan."
    )

    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": test_message,
            "parse_mode": "HTML"
        }
        data = json.dumps(payload).encode("utf-8")
        request_obj = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(request_obj, timeout=10) as response:
            res_body = json.loads(response.read().decode())
            if res_body.get("ok"):
                return {"status": "success", "message": "Pesan tes berhasil terkirim ke Telegram Anda!"}
            else:
                return {"status": "error", "message": f"Telegram API error: {res_body.get('description')}"}
    except Exception as e:
        return {"status": "error", "message": f"Gagal mengirim ke Telegram: {str(e)}"}


# ==========================================
# API Routes: Utilities (Browse & Validation)
# ==========================================
@app.post("/api/open-native-file-dialog")
async def open_native_file_dialog():
    """Membuka dialog file explorer bawaan Windows (Native File Picker)."""
    import queue
    import threading

    res_queue = queue.Queue()

    def _dialog_worker():
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            root.focus_force()
            chosen = filedialog.askopenfilename(
                title="Pilih File Video untuk YouTube Live Streaming",
                filetypes=[
                    ("Video Files (*.mp4, *.mkv, *.flv, *.mov, *.avi, *.ts, *.webm)", "*.mp4;*.mkv;*.flv;*.mov;*.avi;*.ts;*.webm;*.m4v"),
                    ("All Files (*.*)", "*.*")
                ]
            )
            root.destroy()
            res_queue.put(chosen or "")
        except Exception as e:
            res_queue.put(f"ERROR:{e}")

    t = threading.Thread(target=_dialog_worker, daemon=True)
    t.start()
    t.join(timeout=120)

    try:
        file_path = res_queue.get_nowait()
    except queue.Empty:
        return {"status": "error", "message": "Dialog pemilihan file timed out"}

    if file_path.startswith("ERROR:"):
        return {"status": "error", "message": file_path[6:]}

    if not file_path:
        return {"status": "cancelled", "message": "Pemilihan file dibatalkan."}

    norm_path = os.path.normpath(file_path)
    video_info = get_video_info(norm_path)
    return {
        "status": "success",
        "file_path": norm_path,
        "video_info": video_info
    }


@app.get("/api/quick-shortcuts")
async def get_quick_shortcuts():
    """Daftar folder pintasan Windows (Desktop, Videos, Downloads, Drives)."""
    shortcuts = []
    user_home = os.path.expanduser("~")

    # Standard User Folders
    folders = [
        ("Desktop", os.path.join(user_home, "Desktop"), "fa-desktop"),
        ("Videos", os.path.join(user_home, "Videos"), "fa-film"),
        ("Downloads", os.path.join(user_home, "Downloads"), "fa-download"),
        ("Documents", os.path.join(user_home, "Documents"), "fa-file-lines"),
    ]

    for name, path, icon in folders:
        if os.path.exists(path):
            shortcuts.append({"name": name, "path": path, "icon": icon, "is_drive": False})

    # Drives
    if os.name == "nt":
        import string
        for letter in string.ascii_uppercase:
            drive_path = f"{letter}:\\"
            if os.path.exists(drive_path):
                shortcuts.append({"name": f"Drive ({letter}:)", "path": drive_path, "icon": "fa-hard-drive", "is_drive": True})

    return {"status": "success", "data": shortcuts}


@app.post("/api/browse-files")
async def browse_files(req: BrowseRequest):
    """File explorer untuk memilih video di PC secara interaktif."""
    raw_dir = (req.directory or "").strip()
    
    # Deteksi apakah root kosong -> daftar drives
    if not raw_dir or raw_dir == "__ROOT__":
        drives = []
        if os.name == 'nt':
            import string
            for letter in string.ascii_uppercase:
                drive_path = f"{letter}:\\"
                if os.path.exists(drive_path):
                    drives.append({
                        "name": f"Drive ({letter}:)",
                        "path": drive_path,
                        "is_dir": True,
                        "is_drive": True
                    })
        else:
            drives.append({"name": "Home (~)", "path": os.path.expanduser("~"), "is_dir": True, "is_drive": True})

        return {
            "status": "success",
            "current_dir": "",
            "parent_dir": None,
            "breadcrumbs": [{"name": "Komputer (This PC)", "path": "__ROOT__"}],
            "items": drives
        }

    target_dir = os.path.abspath(raw_dir)
    if not os.path.exists(target_dir):
        return {"status": "error", "message": f"Direktori '{target_dir}' tidak ditemukan."}

    # Hitung parent_dir
    norm_target = os.path.normpath(target_dir)
    parent_candidate = os.path.dirname(norm_target)
    
    # Jika target_dir adalah drive root (misal C:\)
    is_drive_root = (norm_target.endswith(":") or norm_target.endswith(":\\") or norm_target.endswith(":/") or parent_candidate == norm_target)
    if is_drive_root:
        parent_dir = "__ROOT__"
    else:
        parent_dir = parent_candidate

    # Hitung breadcrumbs
    breadcrumbs = [{"name": "Komputer", "path": "__ROOT__"}]
    parts = []
    curr = norm_target
    while True:
        p_name = os.path.basename(curr)
        if not p_name:
            # Drive root e.g. "C:\"
            parts.insert(0, {"name": curr, "path": curr})
            break
        else:
            parts.insert(0, {"name": p_name, "path": curr})
            next_curr = os.path.dirname(curr)
            if next_curr == curr:
                break
            curr = next_curr
    breadcrumbs.extend(parts)

    items = []
    video_exts = {".mp4", ".mkv", ".flv", ".mov", ".avi", ".ts", ".webm", ".m4v"}

    try:
        entries = sorted(os.scandir(target_dir), key=lambda e: (not e.is_dir(), e.name.lower()))
        for entry in entries:
            try:
                if entry.name.startswith((".", "$")):
                    continue
                if entry.is_dir():
                    items.append({
                        "name": entry.name,
                        "path": entry.path,
                        "is_dir": True,
                        "is_drive": False
                    })
                elif entry.is_file():
                    ext = os.path.splitext(entry.name)[1].lower()
                    if ext in video_exts:
                        size_mb = round(entry.stat().st_size / (1024 * 1024), 2)
                        items.append({
                            "name": entry.name,
                            "path": entry.path,
                            "is_dir": False,
                            "is_drive": False,
                            "size_mb": size_mb
                        })
            except (PermissionError, OSError):
                continue
    except Exception as e:
        return {"status": "error", "message": f"Gagal membaca direktori: {e}"}

    return {
        "status": "success",
        "current_dir": norm_target,
        "parent_dir": parent_dir,
        "breadcrumbs": breadcrumbs,
        "items": items
    }


@app.post("/api/validate-video")
async def validate_video(req: ValidateVideoRequest):
    info = get_video_info(req.video_path.strip())
    return {"status": "success", "data": info}


@app.get("/api/logs")
async def get_logs(limit: int = 100):
    logs = get_recent_logs(limit=limit)
    return {"status": "success", "data": logs}


if __name__ == "__main__":
    import uvicorn
    print("Memulai YouTube Streaming Server pada http://localhost:8000 ...")
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
