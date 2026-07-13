from . import app, ALLOWED_IMG_EXTENSIONS, ALLOWED_VIDEO_EXTENSIONS, login_manager, GWClient, IdPClient
from flask import render_template, redirect, url_for, flash, request
from login.utils import current_user, login_required, login_user, logout_user, confirm_login, fresh_login_required
from .forms import RegistrationForm, LoginForm, VideoUploadForm, RefreshForm, UpdateAccountForm, UpdateAccountPasswoedForm
from .utils import is_safe_next_url, allowed_file
import requests
import uuid


# ===| Users Auth |===
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

@app.route('/refresh', methods=['GET', 'POST'])
def refresh():
    next_page = request.args.get('next')
    if current_user.is_authenticated and current_user.is_fresh:
        return redirect(url_for('home'))
    form = RefreshForm()
    if form.validate_on_submit():
        redirect_to = redirect(next_page) if next_page and is_safe_next_url(next_page) else redirect(url_for('home'))
        confirm_login(passwd=form.password.data)
        return redirect_to
    return render_template('refresh.html', title='Refresh', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

# ===| User Account |===
@app.route("/account", methods=['GET', 'POST'])
@fresh_login_required
def account():
    info_form = UpdateAccountForm()
    passwd_form = UpdateAccountPasswoedForm()
    if info_form.validate_on_submit():
        IdPClient.changeUserInfo(current_user.id, username=info_form.username.data, email=info_form.email.data)
    if passwd_form.validate_on_submit():
        IdPClient.changeUserPassword(current_user.id, current_passwd=passwd_form.password.data, new_passwd=passwd_form.new_password.data)
    user = IdPClient.getUserInfo(current_user.id)

    refresh_tokens = list()
    for token_id in user["refresh_tokens"]:
        refresh_tokens.append(IdPClient.getRefreshTokenInfo(token_id))
    user["refresh_tokens"] = refresh_tokens

    return render_template('account.html', title=user["username"], info_form=info_form, passwd_form=passwd_form, user=user)

@app.route("/account/revoke")
@fresh_login_required
def revoke_token_pair():
    token_id = request.args.get("id")
    refresh_info = IdPClient.getRefreshTokenInfo(token_id)
    if refresh_info["user_id"] == current_user.id:
        IdPClient.RevokeTokenPair(token_id)
    return redirect(url_for('account'))#.headers.add_header("HX-Refresh", True)

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

        has_img = bool()
        if not img:
            has_img = False
        else:
            if img and allowed_file(img.filename, ALLOWED_IMG_EXTENSIONS):
                has_img = True
            else:
                flash('Image format is incorrect.', 'warning')
                return redirect(url_for('upload'))
        
        upload_id = uuid.uuid4()
        GWClient.upload_file_to_minio(file=video, object_name=f"{upload_id}/video", bucket="uploads", content_type=video.mimetype)
        if has_img:
            GWClient.upload_file_to_minio(file=img, object_name=f"{upload_id}/thumbnail", bucket="uploads", content_type=img.mimetype)
        
        if has_img:
            requests.post(f"http://worker_manager/vid_with_img", json={"upload_id": str(upload_id),
                                                                 "size": form.video.data.content_length,
                                                                 "init_vars": 
                                                                 {  
                                                                    "title": title,
                                                                    "description": "",
                                                                    "author_id": current_user.id
                                                                    },
                                                                 "user_id": current_user.id})
        else:
            requests.post(f"http://worker_manager/vid_without_img", json={"upload_id": str(upload_id),
                                                                 "size": form.video.data.content_length,
                                                                 "init_vars": 
                                                                 {
                                                                    "title": title,
                                                                    "description": "",
                                                                    "author_id": current_user.id
                                                                    },
                                                                 "user_id": current_user.id})

        flash('Video is processing!', 'success')
        return redirect(url_for('home'))
    return render_template('upload.html', active=3, title='Upload', form=form)

@app.route('/video')
def video():
    video_id = request.args.get('id')
    return render_template("player.html", title='Video', video_id=video_id)

@app.route('/search')
def search():
    #query = request.args.get('q')
    return 'In Dev'

@app.route('/stream/<video_id>/<path:file_path>')
def stream_file(video_id, file_path):
    return requests.get(f"http://data_gateway/stream/{video_id}/{file_path}").content

# ===| Home Page |===
@app.route('/')
def home():
    return render_template('index.html', active=1)

@app.route('/load-feed')
def feed():
    offset = int(request.args.get('offset', 0))
    items = GWClient.get_row_from_db(table="videos")
    has_more = offset+21 < len(items)
    return render_template("index_items.html", offset=offset+21, items=items, has_more=has_more)
