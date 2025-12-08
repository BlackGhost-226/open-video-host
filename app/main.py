import json
from flask import render_template, abort, flash, redirect, url_for, request
from jinja2.exceptions import TemplateNotFound
from app import app, logger, db, bcrypt
import os
import app.helper as helper
from app.forms import RegistrationForm, LoginForm, VideoUploadForm, UpdateAccountForm
import app.api as api
from flask_login import login_user, current_user, logout_user
from app.models import User, Video


def home():
    return render_template('index.html', active=1)

def upload():
    form = VideoUploadForm()
    if form.validate_on_submit():
        video = form.video.data
        img = form.thumbnail.data
        text = form.title.data
        api.upload_file(video, img, text)
        flash(f'Video had been uploaded!', 'success')
        return redirect(url_for('home'))
        #return redirect
    return render_template('upload.html', active=3, title='Upload', form=form)

def search(query):
    return render_template('search.html', q=query, title=query)

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

    return render_template('player.html', hls_url=hls_url, dash_url=dash_url, thumbnail_url=thumbnail_url, data_json=data_json, title=data_json['title'])

def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        uesr = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(uesr)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

def login(next_page):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(next_page) if next_page else redirect(url_for('home'))
    return render_template('login.html', title='Login', form=form)

def logout():
    logout_user()
    return redirect(url_for('home'))

def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = helper.save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)

#def open_page(page):
#    try:
#        return render_template(f'{page}.html')
#    except TemplateNotFound:
#        abort(404)
