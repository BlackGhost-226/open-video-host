from flask import request, jsonify
from app import app, SEARCH_COL_NAME, chromadb_client
from flask_login import login_required


# =| main |=
import app.main as main

@app.route('/')
def home():
    return main.home()

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    return main.upload()

@app.route('/register', methods=['GET', 'POST'])
def register():
    return main.register()

@app.route('/login', methods=['GET', 'POST'])
def login():
    next_page = request.args.get('next')
    return main.login(next_page)

@app.route('/video')
def video():
    video_id = request.args.get('id')
    return main.video(video_id)

@app.route('/search')
def search():
    query = request.args.get('q')
    return main.search(query)

@app.route("/account")
@login_required
def account():
    return main.account()

@app.route("/logout")
def logout():
    return main.logout()



# =| api |=
import app.api as api

#@app.route('/api/upload', methods=['POST'])
#def upload_file():
#    return api.upload_file() 

@app.route('/api/stream/<video_id>/<format_type>/<path:filename>')
def stream_file(video_id, format_type, filename):
    key = request.args.get('key', None)
    return api.stream_file(video_id, format_type, filename, key)

@app.route('/api/load-feed')
def load_feed():
    offset = int(request.args.get('offset', 0))
    return api.load_feed(offset)

@app.route('/api/load-search')
def load_search_feed():
    offset = int(request.args.get('offset', 0))
    query = request.args.get('q')
    return api.load_search_feed(offset, query)



# =| debug |=
testing = True
if testing:
    import app.helper as helper

    search_col = chromadb_client.get_collection(name=SEARCH_COL_NAME)
    @app.route('/debug/video-list')
    def video_list():
        return jsonify(helper.video_list())

    @app.route('/debug/vector-list')
    def vector_list():
        get = search_col.get()
        return jsonify(get)

    @app.route('/debug/vector-get')
    def get_v_db():
        query = request.args.get('q')
        results = search_col.query(query_texts=[query], n_results=4)
        return results
