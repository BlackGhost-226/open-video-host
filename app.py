import os
import logging
from flask import Flask, request, jsonify, send_from_directory, render_template
from werkzeug.utils import secure_filename
from flask_cors import CORS
import chromadb


chromadb_client = chromadb.PersistentClient(path=r"./vector-db")
SEARCH_COL_NAME = "search"
try:
    collection = chromadb_client.create_collection(
        name=SEARCH_COL_NAME,
        #embedding_function=None
    )
except:
    pass


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

# Configuration CORS
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'streams'
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm'}
ALLOWED_IMG_EXTENSIONS = {'jpg', 'png'}
MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB max upload size

# Create necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH


import api, main

@app.route('/')
def home():
    return main.home()

@app.route('/<page>')
def open_page(page):
    return main.open_page(page)

@app.route('/video')
def video():
    video_id = request.args.get('id')
    return main.video(video_id)

@app.route('/search')
def search():
    query = request.args.get('q')
    return main.search(query)



@app.route('/api/upload', methods=['POST'])
def upload_file():
    return api.upload_file()
    

@app.route('/api/stream/<video_id>/<format_type>/<path:filename>')
def stream_file(video_id, format_type, filename):
    key = request.args.get('key', None)
    return api.stream_file(video_id, format_type, filename, key)

@app.route('/api/load-feed')
def load_feed():
    offset = int(request.args.get('offset', 0))
    return api.load_feed(offset)



import helper
@app.route('/debug/video-list')
def video_list():
    return jsonify(helper.video_list())

@app.route('/debug/vector-list')
def vector_list():
    return jsonify(helper.vector_list())

if __name__ == '__main__':
    app.run(debug = True)
