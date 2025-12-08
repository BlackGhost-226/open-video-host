import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
from dotenv import load_dotenv
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase

load_dotenv()
app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing


# ===| vector database(for search) |===
chromadb_client = chromadb.PersistentClient(path=r"./vector-db")
SEARCH_COL_NAME = "search"
try:
    collection = chromadb_client.create_collection(
        name=SEARCH_COL_NAME,
        embedding_function=DefaultEmbeddingFunction()
    )
except:
    pass


# ===| logger |===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration CORS
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'streams'
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm'}
ALLOWED_IMG_EXTENSIONS = {'jpg', 'png', 'jpeg', 'gif'}
MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB max upload size

# Creating necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# seting up app configs
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
app.config['SECRET_KEY'] = os.getenv("SK")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'# for SQLAlchemy

class Base(DeclarativeBase):
  pass
db = SQLAlchemy(model_class=Base)
db.init_app(app)

bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

from app import routes
