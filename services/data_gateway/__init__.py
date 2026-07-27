from fastapi import FastAPI
from contextlib import asynccontextmanager
from minio import Minio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pymongo import MongoClient
from os import getenv
from urllib.parse import urlsplit


UPLOAD_BUCKET = "uploads"
OUTPUT_BUCKET = "streams"
PROFILE_BUCKET = "profiles"
MIME_TO_EXT = {
    "video/mp4": "mp4",
    "video/quicktime": "mov",
    "video/webm": "webm",
    "video/x-matroska": "mkv",
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/gif": "gif"
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.mongodb_client = MongoClient(getenv("VECTOR_URI"))
    app.database = app.mongodb_client[getenv("VECTOR_DB_NAME")]

    netloc: dict[str, str] = urlsplit(getenv("S3_URI")).netloc.split("@")
    app.minio_client = Minio(netloc[-1], access_key=netloc[0].split(":")[0], secret_key=netloc[0].split(":")[-1], secure=False)

    def ensure_bucket(bucket: str):
        if not app.minio_client.bucket_exists(bucket):
            app.minio_client.make_bucket(bucket)

    ensure_bucket(UPLOAD_BUCKET)
    ensure_bucket(OUTPUT_BUCKET)
    ensure_bucket(PROFILE_BUCKET)

    engine = create_engine(getenv("DATABASE_URI"))
    connection = engine.connect()
    app.Session = sessionmaker(engine)

    yield

    app.mongodb_client.close()
    connection.close()

app = FastAPI(lifespan=lifespan)

# --| routes |--
from . import minio_routes
from . import sql_routes
#from . import vector_routes
