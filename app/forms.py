from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms.validators import DataRequired, Length, Email, EqualTo
from app import ALLOWED_VIDEO_EXTENSIONS, ALLOWED_IMG_EXTENSIONS

class RegistrationForm(FlaskForm):
    username = StringField('Uesrname', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])

    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')

    submit = SubmitField('Login')

class VideoUploadForm(FlaskForm):
    video = FileField('Video', validators=[FileRequired(), FileAllowed(ALLOWED_VIDEO_EXTENSIONS, f'Invalid Video Format, Valid Formats: {ALLOWED_VIDEO_EXTENSIONS}')])
    thumbnail = FileField('Thumbnail', validators=[FileAllowed(ALLOWED_IMG_EXTENSIONS, f'Invalid Image Format, Valid Formats: {ALLOWED_IMG_EXTENSIONS}')])
    title = StringField('title', validators=[DataRequired()])

    submit = SubmitField('Upload')
