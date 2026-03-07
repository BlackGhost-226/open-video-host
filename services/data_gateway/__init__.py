import os
from fastapi import FastAPI
from minio import Minio

app = FastAPI()

# --| minio |--
minio_client = Minio(
    os.getenv("MINIO_ENDPOINT"),
    access_key=os.getenv("MINIO_ROOT_USER"),
    secret_key=os.getenv("MINIO_ROOT_PASSWORD"),
    secure=False
)

UPLOAD_BUCKET = "uploads"
OUTPUT_BUCKET = "streams"
MIME_TO_EXT = {
    "video/mp4": "mp4",
    "video/quicktime": "mov",
    "video/webm": "webm",
    "video/x-matroska": "mkv"
}


def ensure_bucket(bucket: str):
    if not minio_client.bucket_exists(bucket):
        minio_client.make_bucket(bucket)

ensure_bucket(UPLOAD_BUCKET)
ensure_bucket(OUTPUT_BUCKET)

# --| postgresql |--


# --| routes |--
import minio_routes
import postgresql_routes
