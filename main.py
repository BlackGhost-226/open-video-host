import json
from flask import render_template, abort
from jinja2.exceptions import TemplateNotFound
from app import app, chromadb_client, SEARCH_COL_NAME
import os
import helper


search_col = chromadb_client.get_collection(name=SEARCH_COL_NAME)
#from markupsafe import Markup


#with open('./static/main.html', 'r') as f:
#    main = f.read()
#    main = Markup(main)

def home():
    return render_template('index.html')

def search(query):
    #html = f"""<div class="video">
    #            <a href="{item.video_url}">
    #                <img src="{item.img_url}" alt="cant load img">
    #                <p>{jdata[item.id]["title"]}</p>
    #                <p>{jdata[item.id]["date"]}</p>
    #            </a>
    #        </div>"""
    results = search_col.query(query_texts=[query], n_results=6)["documents"][0]
    return results

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
