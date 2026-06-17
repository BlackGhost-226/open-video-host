from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms.validators import DataRequired, Length, Email, EqualTo
from . import ALLOWED_VIDEO_EXTENSIONS, ALLOWED_IMG_EXTENSIONS

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

class RefreshForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Refresh')

class UpdateAccountForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')

    #def validate_username(self, username):
    #    if username.data != current_user.username:
    #        user = User.query.filter_by(username=username.data).first()
    #        if user:
    #            raise ValidationError('That username is taken. Please choose a different one.')

    #def validate_email(self, email):
    #    if email.data != current_user.email:
    #        user = User.query.filter_by(email=email.data).first()
    #        if user:
    #            raise ValidationError('That email is taken. Please choose a different one.')
