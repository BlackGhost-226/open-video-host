import os
import logging
from dotenv import load_dotenv

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase

import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction


# === Environment Setup ===
load_dotenv()

# === App Initialization ===
app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

# === Logging ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Directory Config ===
#UPLOAD_FOLDER = "uploads"
#OUTPUT_FOLDER = "streams"
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
    SQLALCHEMY_DATABASE_URI="postgresql://test:test@postgresql_db:5432/test",
)


# === Database Setup ===
class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
db.init_app(app)

# === Password Hashing ===
bcrypt = Bcrypt(app)

# === Login Manager ===
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"


# === Vector Database (ChromaDB) ===
CHROMA_PATH = "./vector-db"
SEARCH_COL_NAME = "search"

chromadb_client = chromadb.PersistentClient(path=CHROMA_PATH)

try:
    collection = chromadb_client.create_collection(
        name=SEARCH_COL_NAME,
        embedding_function=DefaultEmbeddingFunction()
    )
except Exception:
    logger.info("ChromaDB collection already exists or could not be created.")


# === Routes Import ===
from app import routes
