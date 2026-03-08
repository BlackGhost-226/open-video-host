import os
import logging
from dotenv import load_dotenv

from flask import Flask
from flask_cors import CORS
from login.login_manager import LoginManager


# === Environment Setup ===
load_dotenv()

# === App Initialization ===
app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

# === Logging ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ui")

# === Directory Config ===
ALLOWED_VIDEO_EXTENSIONS = {"mp4", "avi", "mov", "mkv", "wmv", "flv", "webm"}
ALLOWED_IMG_EXTENSIONS = {"jpg", "png", "jpeg", "gif"}
MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB

#os.makedirs(UPLOAD_FOLDER, exist_ok=True)
#os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# === Flask Config ===
app.config.update(
    #UPLOAD_FOLDER=UPLOAD_FOLDER,
    #OUTPUT_FOLDER=OUTPUT_FOLDER,
    MAX_CONTENT_LENGTH=MAX_CONTENT_LENGTH,
    SECRET_KEY=os.getenv("SK"),
    SQLALCHEMY_DATABASE_URI="postgresql://test:test@postgresql_db:5432/test"
)

# === Login Manager ===
login_manager = LoginManager(IdP_url="http://auth_authority", app=app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"

# === Routes Import ===
from . import routes
