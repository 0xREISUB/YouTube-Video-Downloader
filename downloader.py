import time
import os
import yt_dlp
from utils import format_seconds  # utils'den fonksiyon çektik



class DownloadHandler:
    """İndirme sürecini takip eden sınıf."""

    def __init__(self, socketio, sid, playlist_total=0):
        self.socketio = socketio
        self.sid = sid
        self.playlist_total = playlist_total
        self.start_time = None
        self.last_emit = 0
        self.cached_index = 1 if playlist_total > 1 else 0

    def set_index(self, index):
        """Döngüden gelen index bilgisini günceller."""
        self.cached_index = index

    def hook(self, d):
        # NOT: playlist_index'i artık d'den okumuyoruz çünkü manuel döngüdeyiz.
        # self.cached_index dışarıdan yönetiliyor.

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


def select_format(formats, target_res):
    """
    Belirtilen çözünürlük mantığına göre format seçer.
    Öncelik: Tam Eşleşme -> En Yakın Üst -> En İyi Alt
    """
    try:
        target = int(target_res)
    except ValueError:
        target = 1080

    # Sadece video içeren formatları al
    videos = [f for f in formats if f.get('vcodec') != 'none' and f.get('height')]
    # Yüksekliğe göre artan sıralama (240, 360, 480, 720, 1080...)
    videos.sort(key=lambda x: x['height'])

    if not videos:
        return None

    # 1. Tam Eşleşme (Exact Match)
    exact = [f for f in videos if f['height'] == target]
    if exact:
        # Genelde sonuncusu en yüksek bitrate/kalite olandır
        return exact[-1]['format_id']

    # 2. Higher Fallback (Target yoksa, daha yükseğini ve en yakınını bul)
    # Listem sıralı olduğu için, target'tan büyük olan İLK eleman en yakın üsttür.
    higher = [f for f in videos if f['height'] > target]
    if higher:
        return higher[0]['format_id']

    # 3. Lower Fallback (Hiçbiri yoksa, daha düşüğünü ve en iyisini bul)
    # Listem sıralı olduğu için, target'tan küçük olan SON eleman en iyi alttır.
    lower = [f for f in videos if f['height'] < target]
    if lower:
        return lower[-1]['format_id']

    # Hiçbiri uymazsa
    return 'bestvideo'


def fetch_metadata(url):
    """URL'den metadata çeker (Playlist ise liste, Tek ise tek öğe döner)."""
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True, 'ignoreerrors': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if 'entries' in info:
                # Playlist
                return {
                    'type': 'playlist',
                    'title': info.get('title', 'Playlist'),
                    'entries': [
                        {
                            'index': i+1,
                            'title': entry.get('title', f"Video {i+1}"),
                            'id': entry.get('id', ''),
                            'url': entry.get('url') or entry.get('webpage_url')
                        }
                        for i, entry in enumerate(info['entries']) if entry
                    ]
                }
            else:
                # Tek Video
                return {
                    'type': 'video',
                    'title': info.get('title', 'Video'),
                    'entry': {
                        'index': 1,
                        'title': info.get('title', 'Video'),
                        'id': info.get('id', ''),
                        'url': info.get('webpage_url', url)
                    }
                }
    except Exception as e:
        return {'error': str(e)}


def run_downloader(socketio, url, folder, resolution, sid, selected_indices=None):
    playlist_count = 0
    entries = []

    # 1. Metadata ve Playlist Analizi
    try:
        # extract_flat ile playlist içeriğini hızlıca çekiyoruz
        with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True, 'ignoreerrors': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if 'entries' in info:
                raw_entries = list(info['entries'])
                
                # FİLTRELEME MANTIĞI:
                # Eğer selected_indices varsa, sadece o indexteki videoları al.
                # Indexler 1-based geliyor, o yüzden i+1 kontrolü yapıyoruz.
                if selected_indices and len(selected_indices) > 0:
                    entries = [e for i, e in enumerate(raw_entries) if (i+1) in selected_indices]
                else:
                    entries = raw_entries
                
                playlist_count = len(entries)
            else:
                # Tek video
                entries = [info]
                playlist_count = 1

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

    # 2. İndirme Döngüsü
    handler = DownloadHandler(socketio, sid, playlist_count)

    success_count = 0
    
    # enumerate'i artık filtrelenmiş liste üzerinde yapıyoruz.
    # Ancak orijinal index korunmalı mı?
    # Kullanıcı "3. videoyu indir" dediyse, kaydedilen dosya adı "03 - Video..." mu olmalı yoksa "01 - Video..." mu?
    # Genelde playlist indiricilerde orijinal sıra numarası korunur.
    # Ancak burada basitleştirmek için, ve 'entries' listesi orijinal sırayı koruduğu için (sadece atlananlar var),
    # biz yine de orijinal index'i bulmaya çalışabiliriz veya sadece kaçıncı indirdiğimizi sayabiliriz.
    # Youtube-DL'in 'playlist_index' özelliği filtrelemede karışabilir.
    # Basitçe: İndirirken dosya adına 'playlist_index'i yt-dlp'den almasını söylersek, yt-dlp bunu extract_flat'ten gelen bilgiyle
    # eşleşmeyebilir eğer manuel loop yapıyorsak.
    # ÇÖZÜM: enumerate ile dönüyoruz, ama bu 'processed index' olur.
    # Dosya adını manuel veriyoruz. Orijinal sırayı korumak istersek extract sırasında index bilgisini saklamalıydık.
    # Şimdilik kullanıcıya gösterilen (1/5) formatı "Processing 1 of 5 selected" şeklinde olacak.
    
    for i, entry in enumerate(entries):
        # İşlenen video sayısı (1-based)
        current_proc_index = i + 1
        handler.set_index(current_proc_index)

        # Video URL'sini al (entry bazen id, bazen url döner)
        video_url = entry.get('url') or entry.get('webpage_url')
        if not video_url: # Bazen id döner, url oluşturmak gerekebilir ama yt-dlp genelde url verir
             if entry.get('id'):
                 video_url = f"https://www.youtube.com/watch?v={entry['id']}"
             else:
                 continue # URL yoksa geç

        try:
            # Format Seçimi için Video Bilgisi Çek
            # (Tekil video analizi)
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl_temp:
                 vid_info = ydl_temp.extract_info(video_url, download=False)
            
            target_fid = select_format(vid_info.get('formats', []), resolution)
            
            if not target_fid:
                target_fid = "bestvideo"

            # İndirme Ayarları
            if playlist_count > 1:
                # Playlist ise numaralandır (İşleme sırasına göre veriyoruz şimdilik)
                # Alternatif: entry['playlist_index'] varsa onu kullan.
                pl_idx = entry.get('playlist_index') or current_proc_index
                out_template = os.path.join(folder, f"{pl_idx:02d} - %(title)s.%(ext)s")
            else:
                out_template = os.path.join(folder, "%(title)s.%(ext)s")

            opts = {
                "outtmpl": out_template,
                "progress_hooks": [handler.hook],
                # Seçilen video formatı + en iyi ses
                "format": f"{target_fid}+bestaudio/best",
                "merge_output_format": "mp4",
                "quiet": True,
                "nocheckcertificate": True,
                "ignoreerrors": True
            }

            # İndirmeyi Başlat
            with yt_dlp.YoutubeDL(opts) as ydl_final:
                ydl_final.download([video_url])
            
            success_count += 1

        except Exception as e:
            print(f"Video Hatası ({current_proc_index}): {e}")
            # Hata olsa bile playlist devam etsin
            continue
    
    # Bitiş Mesajı
    if success_count > 0:
        socketio.emit('done', {'msg': f"İşlem tamamlandı. {success_count}/{playlist_count} video indirildi."}, to=sid)
    else:
        socketio.emit('error', {'msg': "Hiçbir video indirilemedi."}, to=sid)