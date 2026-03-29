from . import app, ALLOWED_IMG_EXTENSIONS, ALLOWED_VIDEO_EXTENSIONS, login_manager
from flask import render_template, redirect, url_for, flash, request
from login.utils import current_user, login_required, login_user, logout_user
from .forms import RegistrationForm, LoginForm, VideoUploadForm
from .utils import is_safe_next_url, allowed_file
import requests
from werkzeug.utils import secure_filename
import uuid


@app.route('/')
def home():
    return render_template('index.html', active=1)

# ===| Users |===
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        login_manager.IdPClient.createUser(name=form.username.data, email=form.email.data, passwd=form.password.data)
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    next_page = request.args.get('next')
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        redirect_to = redirect(next_page) if next_page and is_safe_next_url(next_page) else redirect(url_for('home'))
        login_user(email=form.email.data, password=form.password.data, remember=form.remember.data)
        return redirect_to
    return render_template('login.html', title='Login', form=form)

@app.route("/account")
@login_required
def account():
    return 'test'

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

# ===| Videos |===
@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    form = VideoUploadForm()
    if form.validate_on_submit():
        video = form.video.data
        img = form.thumbnail.data
        title = form.title.data

        if not allowed_file(video.filename, ALLOWED_VIDEO_EXTENSIONS):
            flash('Video format is incorrect.', 'warning')
            return redirect(url_for('upload'))

        has_img = bool
        if not img:
            has_img = False
        else:
            if img and allowed_file(img.filename, ALLOWED_IMG_EXTENSIONS):
                has_img = True
            else:
                flash('Image format is incorrect.', 'warning')
                return redirect(url_for('upload'))
        
        upload_id = uuid.uuid4()

        upload_url = requests.get(f"http://data_gateway/minio/upload-url?object_name={upload_id}/video").json()["upload_url"]
        requests.put(url=upload_url,
                     data=video,
                     headers={
                        "Content-Type": video.mimetype
                        }
                    )

        if has_img:
            upload_url = requests.get(f"http://data_gateway/minio/upload-url?object_name={upload_id}/thumbnail").json()["upload_url"]
            requests.put(url=upload_url,
                        data=img,
                        headers={
                            "Content-Type": img.mimetype
                            }
                        )
        
        requests.post(f"http://worker_manager/new-upload", json={"upload_id": str(upload_id),
                                                                 "video_size": form.video.data.content_length,
                                                                 "title": title,
                                                                 "description": "",
                                                                 "user_id": current_user.id})

        flash('Video is processing!', 'success')
        return redirect(url_for('home'))
    return render_template('upload.html', active=3, title='Upload', form=form)

@app.route('/video')
def video():
    video_id = request.args.get('id')
    return render_template("player.html", title='Video',
                            dash_url=f"http://127.0.0.1:33/stream/{video_id}/dash/manifest.mpd",
                            hls_url=f"http://127.0.0.1:33/stream/{video_id}/hls/playlist.m3u8")

@app.route('/search')
def search():
    #query = request.args.get('q')
    return 'test'
