import os
from app import app, chromadb_client, SEARCH_COL_NAME, logger
from werkzeug.utils import secure_filename
from typing import Callable
from flask import render_template
import json

search_col = chromadb_client.get_collection(name=SEARCH_COL_NAME)


def allowed_file(filename: str, ae: list):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ae

def video_list():
    videos = []

    # Get all subdirectories in the streams folder
    for video_id in os.listdir(app.config['OUTPUT_FOLDER']):
        video_dir = os.path.join(app.config['OUTPUT_FOLDER'], video_id)

        if os.path.isdir(video_dir):
            hls_path = os.path.join(video_dir, 'hls', 'playlist.m3u8')
            dash_path = os.path.join(video_dir, 'dash', 'manifest.mpd')

            if os.path.exists(hls_path) or os.path.exists(dash_path):
                videos.append(generate_video_json(video_id))
    return videos

def vector_list():
    get = search_col.get()
    return get

def secure_save(file: str, upload_dir: str):
    filename = secure_filename(file.filename)
    file_path = os.path.join(upload_dir, filename)
    file.save(file_path)
    return file_path

def compress_file(file_path: str, compress_func: Callable):
    os.rename(file_path, file_path+".temp")
    com = compress_func(file_path+".temp", file_path)
    if not com:
        return False
    os.remove(file_path+".temp")
    return True

def generate_video_json(video_id):
    return {'id': video_id,
            'hls_url': f'/api/stream/{video_id}/hls/playlist.m3u8',
            'dash_url': f'/api/stream/{video_id}/dash/manifest.mpd',
            'video_url': f'/video?id={video_id}',
            'img_url': f'/api/stream/{video_id}/data/thumbnail.jpg',
            "data_url": f'/api/stream/{video_id}/data/data.json'
            }

def load_template(offset, items, offset_number, item_html, **kwargs):
    # Load the next 21 items
    next_items = items[offset:offset+offset_number]
    
    # Check if there are more items to load
    has_more = offset + offset_number < len(items)

    jdata = {}
    for item in next_items:
        directory = os.path.join(app.config['OUTPUT_FOLDER'], item["id"], "data")
        with open(directory+"/data.json", "r") as f:
            data_json = json.load(f)
            jdata[item["id"]] = data_json

    return render_template(item_html, items=next_items, offset=offset+offset_number, has_more=has_more, jdata=jdata, **kwargs)
