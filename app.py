import eventlet
eventlet.monkey_patch()  # Asenkron işlemler için gerekli patch

import os
import sys
import time
import subprocess
import yt_dlp
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO

# Tkinter import işlemi (Windows dosya seçimi için)
try:
    import tkinter as tk
    from tkinter import filedialog
except ImportError:
    tk = None

app = Flask(__name__)
# Bağlantı kararlılığı için ping ayarları
socketio = SocketIO(app, async_mode="eventlet", cors_allowed_origins="*", ping_timeout=60, ping_interval=25)

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

class DownloadHandler:
    """İndirme sürecini takip eden ve SocketIO ile istemciye veri gönderen sınıf."""
    
    def __init__(self, sid, playlist_total=0):
        self.sid = sid
        self.playlist_total = playlist_total
        self.start_time = None
        self.last_emit = 0
        # yt-dlp her pakette index göndermediği için son indexi hafızada tutuyoruz
        self.cached_index = 1 if playlist_total > 1 else 0

    def hook(self, d):
        # Playlist index güncellemesi
        if 'playlist_index' in d:
            self.cached_index = d['playlist_index']
        elif d.get('info_dict') and 'playlist_index' in d['info_dict']:
             self.cached_index = d['info_dict']['playlist_index']

        # Temel video bilgileri
        info = d.get('info_dict', {})
        title = info.get('title', 'Bilinmeyen Video')
        thumbnail = info.get('thumbnail', '')

        # Durum: İndiriliyor
        if d['status'] == 'downloading':
            if self.start_time is None:
                self.start_time = time.time()

            # İlerleme ve hız hesaplamaları
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            percent = (downloaded / total * 100) if total else 0

            elapsed = time.time() - self.start_time
            speed = downloaded / elapsed if elapsed > 1 else 0
            speed_str = f"{speed/1024/1024:.1f} MB/s" if speed else "-- MB/s"
            eta_str = format_seconds((total - downloaded) / speed) if speed else "--:--"

            data = {
                'status': 'downloading',
                'title': title,
                'thumbnail': thumbnail,
                'percent': round(percent, 1),
                'speed': speed_str,
                'eta': eta_str,
                'is_playlist': self.playlist_total > 1,
                'playlist_index': self.cached_index,
                'playlist_total': self.playlist_total
            }

            # Playlist genel yüzdesi hesaplama
            if self.playlist_total > 1:
                 current_calc_index = self.cached_index if self.cached_index > 0 else 1
                 global_percent = ((current_calc_index - 1) * 100 + percent) / self.playlist_total
                 data['playlist_percent'] = round(global_percent, 1)

            # UI performansını korumak için veri gönderimini sınırla (0.2s)
            now = time.time()
            if now - self.last_emit > 0.2:
                socketio.emit('progress', data, to=self.sid)
                self.last_emit = now
                socketio.sleep(0)

        # Durum: İndirme Bitti / İşleniyor
        elif d['status'] == 'finished':
            data = {
                'status': 'processing',
                'title': title,
                'thumbnail': thumbnail,
                'percent': 100,
                'is_playlist': self.playlist_total > 1,
                'playlist_index': self.cached_index,
                'playlist_total': self.playlist_total,
                'playlist_percent': round((self.cached_index * 100) / self.playlist_total, 1) if self.playlist_total > 1 else 100
            }
            socketio.emit('progress', data, to=self.sid)
            socketio.sleep(0)
            self.start_time = None

# --- Rotalar ---

@app.route('/')
def index():
    return render_template('index.html', default_path=get_default_path())

@app.route('/select-folder', methods=['POST'])
def select_folder_route():
    return jsonify({'path': open_folder_dialog()})

@socketio.on('start_download')
def start_download(data):
    socketio.start_background_task(run_downloader, data['url'], data['path'], request.sid)

def run_downloader(url, folder, sid):
    playlist_count = 0
    
    # 1. Metadata Analizi
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            if 'entries' in info:
                playlist_count = len(info['entries'])
            
            socketio.emit('metadata', {
                'title': info.get('title', 'İndirme Başlatılıyor...'),
                'thumbnail': info.get('thumbnail', ''),
                'is_playlist': playlist_count > 1,
                'playlist_total': playlist_count
            }, to=sid)
            socketio.sleep(0)

    except Exception as e:
        socketio.emit('error', {'msg': f"Bağlantı Hatası: {str(e)}"}, to=sid)
        return

    # 2. İndirme Yapılandırması
    handler = DownloadHandler(sid, playlist_count)
    template = "%(playlist_index)s - %(title)s.%(ext)s" if playlist_count > 1 else "%(title)s.%(ext)s"

    opts = {
        "outtmpl": os.path.join(folder, template),
        "progress_hooks": [handler.hook],
        "format": "bv*+ba/b",
        "merge_output_format": "mp4",
        "quiet": True,
        "nocheckcertificate": True,
        "ignoreerrors": True
    }

    # 3. İndirme Başlatma
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        socketio.emit('done', {'msg': "İşlem başarıyla tamamlandı."}, to=sid)
    except Exception as e:
        socketio.emit('error', {'msg': f"İndirme Hatası: {str(e)}"}, to=sid)

if __name__ == "__main__":
    # Güvenlik: Sadece localhost (127.0.0.1) üzerinden erişim.
    # Port: 8999
    print("Server is running at: http://127.0.0.1:8999")
    socketio.run(app, host="127.0.0.1", port=8999, debug=False)