from app import app, bcrypt, db
from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required, login_user, logout_user
from app.models import User, Video
from app.forms import RegistrationForm, LoginForm

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
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        uesr = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(uesr)
        db.session.commit()
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
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(next_page) if next_page else redirect(url_for('home'))
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
    return 'test'

@app.route('/video')
def video():
    #video_id = request.args.get('id')
    return 'test'

@app.route('/search')
def search():
    #query = request.args.get('q')
    return 'test'
