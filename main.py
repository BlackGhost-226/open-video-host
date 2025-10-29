import json
from flask import render_template, abort
from jinja2.exceptions import TemplateNotFound
from app import app
import os
import helper


#from markupsafe import Markup


#with open('./static/main.html', 'r') as f:
#    main = f.read()
#    main = Markup(main)

def home():
    return render_template('index.html')

def search(query):
    return render_template('search.html', q=query)

def video(video_id):
    """Render the video player page"""
    # Make sure we're explicitly passing video_id to the template
    video_data = helper.generate_video_json(video_id)
    hls_url = video_data['hls_url']
    dash_url = video_data['dash_url']
    thumbnail_url = video_data['img_url']

    directory = os.path.join(app.config['OUTPUT_FOLDER'], video_id, "data")
    with open(directory+"/data.json", "r") as f:
        data_json = json.load(f)

    return render_template('player.html', hls_url=hls_url, dash_url=dash_url, thumbnail_url=thumbnail_url, data_json=data_json)

def open_page(page):
    try:
        return render_template(f'{page}.html')
    except TemplateNotFound:
        abort(404)
