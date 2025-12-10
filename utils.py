import os
import sys
import subprocess

# Tkinter import işlemi (Windows dosya seçimi için)
try:
    import tkinter as tk
    from tkinter import filedialog
except ImportError:
    tk = None


def get_default_path():
    """Kullanıcının varsayılan 'Downloads' klasörünü bulur."""
    home = os.path.expanduser("~")
    download_path = os.path.join(home, "Downloads")

    if not os.path.exists(download_path):
        return home
    return download_path


def format_seconds(seconds):
    """Saniyeyi SA:DK:SN formatına çevirir."""
    if not seconds or seconds < 0:
        return "--:--"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def open_folder_dialog():
    """İşletim sistemine uygun klasör seçme penceresini açar."""
    start_path = get_default_path()

    # Linux için Zenity (Nautilus arayüzü) öncelikli
    if sys.platform != 'win32':
        try:
            cmd = [
                'zenity',
                '--file-selection',
                '--directory',
                '--title=Klasör Seç',
                f'--filename={start_path}/'
            ]
            return subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode().strip()
        except:
            pass  # Zenity yoksa Tkinter'a düş

    # Windows veya Zenity olmayan sistemler için Tkinter
    if tk:
        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            selected_path = filedialog.askdirectory(initialdir=start_path, title="Klasör Seç")
            root.destroy()
            return selected_path
        except:
            return ""
    return ""