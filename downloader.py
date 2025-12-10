import time
import os
import yt_dlp
from utils import format_seconds  # utils'den fonksiyon çektik


class DownloadHandler:
    """İndirme sürecini takip eden sınıf."""

    # socketio nesnesini dışarıdan alacak şekilde güncelledik
    def __init__(self, socketio, sid, playlist_total=0):
        self.socketio = socketio
        self.sid = sid
        self.playlist_total = playlist_total
        self.start_time = None
        self.last_emit = 0
        self.cached_index = 1 if playlist_total > 1 else 0

    def hook(self, d):
        # Playlist index güncellemesi
        if 'playlist_index' in d:
            self.cached_index = d['playlist_index']
        elif d.get('info_dict') and 'playlist_index' in d['info_dict']:
            self.cached_index = d['info_dict']['playlist_index']

        info = d.get('info_dict', {})
        title = info.get('title', 'Bilinmeyen Video')
        thumbnail = info.get('thumbnail', '')

        if d['status'] == 'downloading':
            if self.start_time is None:
                self.start_time = time.time()

            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            percent = (downloaded / total * 100) if total else 0

            elapsed = time.time() - self.start_time
            speed = downloaded / elapsed if elapsed > 1 else 0
            speed_str = f"{speed / 1024 / 1024:.1f} MB/s" if speed else "-- MB/s"
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

            if self.playlist_total > 1:
                current_calc_index = self.cached_index if self.cached_index > 0 else 1
                global_percent = ((current_calc_index - 1) * 100 + percent) / self.playlist_total
                data['playlist_percent'] = round(global_percent, 1)

            now = time.time()
            if now - self.last_emit > 0.2:
                self.socketio.emit('progress', data, to=self.sid)
                self.last_emit = now
                self.socketio.sleep(0)

        elif d['status'] == 'finished':
            data = {
                'status': 'processing',
                'title': title,
                'thumbnail': thumbnail,
                'percent': 100,
                'is_playlist': self.playlist_total > 1,
                'playlist_index': self.cached_index,
                'playlist_total': self.playlist_total,
                'playlist_percent': round((self.cached_index * 100) / self.playlist_total,
                                          1) if self.playlist_total > 1 else 100
            }
            self.socketio.emit('progress', data, to=self.sid)
            self.socketio.sleep(0)
            self.start_time = None


def run_downloader(socketio, url, folder, sid):
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
    # socketio nesnesini handler'a veriyoruz
    handler = DownloadHandler(socketio, sid, playlist_count)
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