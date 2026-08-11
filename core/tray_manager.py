import os
import sys
import ctypes
import webbrowser
import threading
from PIL import Image
import pystray
from pystray import MenuItem as item
from core.config import BASE_DIR, add_log


class TrayManager:
    def __init__(self, port: int = 8000):
        self.port = port
        self.icon = None
        self._is_console_hidden = False
        self._hwnd = None

    def _get_hwnd(self):
        if sys.platform != 'win32':
            return None
        
        # 1. Coba GetConsoleWindow
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            self._hwnd = hwnd
            return hwnd

        # 2. Coba FindWindowW berdasarkan judul jendela
        hwnd_by_title = ctypes.windll.user32.FindWindowW(None, "YouTube Scheduled Stream Server (StreamYT Pro)")
        if hwnd_by_title:
            self._hwnd = hwnd_by_title
            return hwnd_by_title

        # 3. Coba Enumerasi Jendela
        found_hwnds = []
        def _enum_proc(h, lparam):
            if ctypes.windll.user32.IsWindow(h):
                length = ctypes.windll.user32.GetWindowTextLengthW(h)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    ctypes.windll.user32.GetWindowTextW(h, buff, length + 1)
                    title = buff.value
                    if "StreamYT" in title or "YouTube Scheduled Stream" in title:
                        found_hwnds.append(h)
            return True

        try:
            WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
            ctypes.windll.user32.EnumWindows(WNDENUMPROC(_enum_proc), 0)
            if found_hwnds:
                self._hwnd = found_hwnds[0]
                return found_hwnds[0]
        except Exception:
            pass

        return self._hwnd

    def toggle_console(self, icon=None, item=None):
        if sys.platform != 'win32':
            return
        hwnd = self._get_hwnd()
        if not hwnd:
            return
        if self._is_console_hidden:
            ctypes.windll.user32.ShowWindow(hwnd, 5)  # SW_SHOW = 5
            self._is_console_hidden = False
            add_log("INFO", "Jendela CMD ditampilkan kembali", "SYSTEM")
        else:
            ctypes.windll.user32.ShowWindow(hwnd, 0)  # SW_HIDE = 0
            self._is_console_hidden = True
            add_log("INFO", "Jendela CMD disembunyikan ke System Tray", "SYSTEM")

    def hide_console(self):
        if sys.platform != 'win32':
            return
        hwnd = self._get_hwnd()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)  # SW_HIDE = 0
            self._is_console_hidden = True
            add_log("INFO", "Jendela CMD disembunyikan ke System Tray", "SYSTEM")

    def show_console(self):
        if sys.platform != 'win32':
            return
        hwnd = self._get_hwnd()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 5)  # SW_SHOW = 5
            self._is_console_hidden = False
            add_log("INFO", "Jendela CMD ditampilkan kembali", "SYSTEM")

    def open_browser(self, icon=None, item=None):
        webbrowser.open(f"http://localhost:{self.port}")

    def exit_app(self, icon=None, item=None):
        from core.stream_engine import stream_engine
        try:
            stream_engine.stop_stream()
        except Exception:
            pass
        if self.icon:
            self.icon.stop()
        self.show_console()
        os._exit(0)

    def run_tray(self):
        icon_path = os.path.join(BASE_DIR, "icon_square.png")
        if not os.path.exists(icon_path):
            icon_path = os.path.join(BASE_DIR, "icon.png")

        if os.path.exists(icon_path):
            try:
                raw_img = Image.open(icon_path)
                if raw_img.mode != 'RGBA':
                    raw_img = raw_img.convert('RGBA')
                w, h = raw_img.size
                max_dim = max(w, h)
                square_img = Image.new('RGBA', (max_dim, max_dim), (0, 0, 0, 0))
                square_img.paste(raw_img, ((max_dim - w) // 2, (max_dim - h) // 2))
                image = square_img.resize((64, 64), Image.Resampling.LANCZOS)
            except Exception:
                image = Image.new('RGB', (64, 64), color=(255, 0, 51))
        else:
            image = Image.new('RGB', (64, 64), color=(255, 0, 51))

        menu = pystray.Menu(
            item('🌐 Buka Dashboard Web', self.open_browser, default=True),
            item('👁️ Tampilkan / Sembunyikan CMD', self.toggle_console),
            pystray.Menu.SEPARATOR,
            item('❌ Keluar & Tutup Server', self.exit_app)
        )

        try:
            self.icon = pystray.Icon("StreamYT", image, "StreamYT Pro - YouTube Live Scheduler", menu)
            self.icon.run()
        except Exception as e:
            add_log("WARN", f"System Tray tidak aktif di lingkungan ini: {e}", "SYSTEM")

    def start_in_background(self):
        t = threading.Thread(target=self.run_tray, daemon=True)
        t.start()


# Global Singleton
tray_manager = TrayManager(port=8000)
