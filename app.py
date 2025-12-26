import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO

# Yeni modüllerimizi çağırıyoruz
from utils import get_default_path, open_folder_dialog
from downloader import run_downloader, fetch_metadata

app = Flask(__name__)
socketio = SocketIO(app, async_mode="eventlet", cors_allowed_origins="*", ping_timeout=60, ping_interval=25)

@app.route('/')
def index():
    return render_template('index.html', default_path=get_default_path())

@app.route('/select-folder', methods=['POST'])
def select_folder_route():
    return jsonify({'path': open_folder_dialog()})

@socketio.on('fetch_metadata')
def handle_fetch_metadata(data):
    def background_fetch(url, sid):
        result = fetch_metadata(url)
        socketio.emit('metadata_result', result, to=sid)
    
    socketio.start_background_task(background_fetch, data['url'], request.sid)

@socketio.on('start_download')
def start_download(data):
    # run_downloader fonksiyonuna socketio nesnesini de gönderiyoruz
    resolution = data.get('resolution', '1080')
    indices = data.get('indices', []) # Seçilen index listesi (boşsa hepsi)
    socketio.start_background_task(run_downloader, socketio, data['url'], data['path'], resolution, request.sid, indices)

if __name__ == "__main__":
    print("Server is running at: http://127.0.0.1:8999")
    socketio.run(app, host="127.0.0.1", port=8999, debug=True)