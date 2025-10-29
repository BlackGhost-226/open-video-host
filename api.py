import json
import threading
from app import app, logger, ALLOWED_VIDEO_EXTENSIONS, ALLOWED_IMG_EXTENSIONS, chromadb_client, SEARCH_COL_NAME
from flask import request, jsonify, send_from_directory, render_template
import helper
import uuid
import os
from process_video import process_video


search_col = chromadb_client.get_collection(name=SEARCH_COL_NAME)

def upload_file():
    video = request.files.get('video')
    img = request.files.get('img')
    text = request.form.get('text')

    #if text sql enj:

    has_img = bool
    if img is None:
        has_img = False
    else:
        if img and helper.allowed_file(img.filename, ALLOWED_IMG_EXTENSIONS):
            has_img = True
        else:
            return jsonify({'error': 'Image file type not allowed'}), 400

    if video and helper.allowed_file(video.filename, ALLOWED_VIDEO_EXTENSIONS):
        # Generate a unique ID for this video
        video_id = str(uuid.uuid4())

        # Create directories for this video
        video_upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], video_id)
        os.makedirs(video_upload_dir, exist_ok=True)

        stream_output_dir = os.path.join(app.config['OUTPUT_FOLDER'], video_id)
        os.makedirs(stream_output_dir, exist_ok=True)

        # Save the original file
        video_path = helper.secure_save(video, video_upload_dir)
        if has_img:
            img_path = helper.secure_save(img, video_upload_dir)

        data = {
            "title": text
        }

        # video to search db
        search_col.add(
            ids=[text],
            documents=[video_id]
        )
        
        if has_img:
            threading.Thread(target=process_video, args=(stream_output_dir, video_upload_dir, video_path, has_img, img_path, data,)).start()
        else:
            threading.Thread(target=process_video, args=(stream_output_dir, video_upload_dir, video_path, has_img, None, data,)).start()
        
        return jsonify({
            'id': video_id,
            'video_url': f'/video?id={video_id}',
            'status': 'succes'
        })

    return jsonify({'error': 'Video file type not allowed'}), 400

def stream_file(video_id, format_type, filename, key):
    """Serve the video stream files"""
    directory = os.path.join(app.config['OUTPUT_FOLDER'], video_id, format_type)
    response =  send_from_directory(directory, filename)

    if response.mimetype == "application/json":
        with open(f"{directory}/{filename}", "r") as f:
            if key is None or key == '':
                response = json.load(f)
            else:
                response = json.load(f)[key]

    return response

def load_feed(offset):
    items = helper.video_list()
    
    return helper.load_template(offset=offset, item_html='home_items.html', items=items, offset_number=21)

def load_search_feed(offset, query):
    items = []
    results = search_col.query(query_texts=[query], n_results=6)["documents"][0]
    for result in results:
        items.append(helper.generate_video_json(result))

    return helper.load_template(offset=offset, item_html='search_items.html', items=items, offset_number=4, q=query)
