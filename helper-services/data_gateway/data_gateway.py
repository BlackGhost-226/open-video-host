import os
from fastapi import FastAPI, HTTPException
from minio import Minio
from datetime import timedelta

app = FastAPI()


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

@app.get("/minio/upload-url")
def create_upload_url(object_name: str, bucket: str = UPLOAD_BUCKET):
    """
    Returns a URL to upload a file directly to MinIO
    """
    try:
        url = minio_client.presigned_put_object(
            bucket,
            object_name,
            expires=timedelta(hours=1)
        )
        return {
            "bucket": bucket,
            "object": object_name,
            "upload_url": url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/minio/download-url")
def create_download_url(object_name: str, bucket: str = OUTPUT_BUCKET):
    """
    Returns a URL to download a file
    """
    try:
        url = minio_client.presigned_get_object(
            bucket,
            object_name,
            expires=timedelta(hours=1)
        )

        stat = minio_client.stat_object(bucket, object_name)

        fmt = (
            stat.metadata.get("x-amz-meta-format")
            or MIME_TO_EXT.get(stat.content_type)
        )

        return {
            "bucket": bucket,
            "object": object_name,
            "download_url": url,
            "format": fmt
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/minio/video-upload")
def video_upload(title: str):
    pass

#@app.get("/minio/delete-object")
def delete_object(bucket: str, object_name: str):
    """
    Deletes an object from MinIO.
    """
    try:
        minio_client.remove_object(bucket, object_name)
        return {
            "status": "deleted",
            "bucket": bucket,
            "object": object_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
