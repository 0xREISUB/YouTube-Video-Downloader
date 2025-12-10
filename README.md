# 🚀 YT Pro Downloader

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/Flask-2.0%2B-green)
![License](https://img.shields.io/badge/License-MIT-orange)

[🇬🇧 English](#-english) | [🇹🇷 Türkçe](#-türkçe)

---

## 🇬🇧 English

**YT Pro Downloader** is a modern, web-based tool designed to download videos and playlists from YouTube. It features a sleek "Glassmorphism" UI, real-time progress tracking via WebSockets, and automatic format merging.

### ✨ Features
* **Video & Playlist Support:** Downloads single videos or entire playlists seamlessly.
* **Real-Time Progress:** Shows download speed, ETA, and percentage instantly via Socket.IO.
* **Smart Folder Selection:**
    * **Linux:** Uses native Zenity dialogs (Nautilus style).
    * **Windows:** Falls back to Tkinter dialogs automatically.
* **Modern UI:** Dark mode with Glassmorphism design and smooth animations.
* **Privacy Focused:** Runs locally on `127.0.0.1`, inaccessible from outside networks.

### 🛠 Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/USERNAME/YT-Pro-Downloader.git](https://github.com/USERNAME/YT-Pro-Downloader.git)
    cd YT-Pro-Downloader
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **System Requirement (Linux Only):**
    Ensure `ffmpeg` and `zenity` are installed for full functionality.
    ```bash
    sudo apt install ffmpeg zenity
    ```

### ▶️ Usage

1.  Run the application:
    ```bash
    python3 app.py
    ```
2.  Open your browser and go to:
    `http://127.0.0.1:8999`

---

## 🇹🇷 Türkçe

**YT Pro Downloader**, YouTube üzerinden video ve oynatma listelerini indirmek için tasarlanmış modern, web tabanlı bir araçtır. Şık "Glassmorphism" arayüzü, WebSocket üzerinden anlık ilerleme takibi ve otomatik format birleştirme özelliklerine sahiptir.

### ✨ Özellikler
* **Video ve Playlist Desteği:** Tekli videoları veya tüm oynatma listesini sorunsuz indirir.
* **Anlık Takip:** İndirme hızı, kalan süre ve yüzdeyi Socket.IO ile saniyesi saniyesine gösterir.
* **Akıllı Klasör Seçimi:**
    * **Linux:** Yerel Zenity pencerelerini kullanır (Nautilus tarzı).
    * **Windows:** Otomatik olarak Tkinter penceresine geçer.
* **Modern Arayüz:** Glassmorphism tasarımlı, animasyonlu karanlık mod (Dark Mode).
* **Gizlilik Odaklı:** Sadece `127.0.0.1` (Localhost) üzerinde çalışır, dış ağlardan erişilemez.

### 🛠 Kurulum

1.  **Repoyu klonlayın:**
    ```bash
    git clone [https://github.com/KULLANICI_ADIN/YT-Pro-Downloader.git](https://github.com/KULLANICI_ADIN/YT-Pro-Downloader.git)
    cd YT-Pro-Downloader
    ```

2.  **Gereksinimleri yükleyin:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Sistem Gereksinimi (Sadece Linux):**
    Tam performans için `ffmpeg` ve `zenity` yüklü olmalıdır.
    ```bash
    sudo apt install ffmpeg zenity
    ```

### ▶️ Kullanım

1.  Uygulamayı başlatın:
    ```bash
    python3 app.py
    ```
2.  Tarayıcınızda şu adrese gidin:
    `http://127.0.0.1:8999`

---

## ⚠️ Disclaimer / Yasal Uyarı

> **English:** This project is developed strictly for educational and personal use. Downloading copyrighted material without permission may violate YouTube's Terms of Service. The user is solely responsible for ensuring compliant usage. The developer accepts no liability for misuse.

> **Türkçe:** Bu proje tamamen eğitim ve kişisel kullanım amaçlı geliştirilmiştir. Telif hakkı ile korunan materyallerin izinsiz indirilmesi YouTube Hizmet Koşullarına aykırı olabilir. Aracı yasalara uygun şekilde kullanmak tamamen kullanıcının sorumluluğundadır. Geliştirici, kötüye kullanım durumunda sorumluluk kabul etmez.

---
*Developed with ❤️ using Flask & Socket.IO*
