import os
from . import app
from werkzeug.utils import secure_filename
from typing import Callable
from flask import render_template
import json
from urllib.parse import urlparse


def allowed_file(filename: str, ae: list):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ae

def is_safe_next_url(target: str) -> bool:
    if not target:
        return False
    parsed = urlparse(target)
    return parsed.scheme == "" and parsed.netloc == ""

def compress_file(file_path: str, compress_func: Callable):
    os.rename(file_path, file_path+".temp")
    com = compress_func(file_path+".temp", file_path)
    if not com:
        return False
    os.remove(file_path+".temp")
    return True

def load_item_template(offset, items, offset_number, item_html, **kwargs):
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


#def save_picture(picture):
#    picture_id = uuid.uuid4()
#    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_id)
#
#    output_size = (125, 125)
#    i = Image.open(picture)
#    i.thumbnail(output_size)
#    i.save(picture_path)
#
#    return picture_id
