from data_gateway import app, minio_client, UPLOAD_BUCKET, OUTPUT_BUCKET, MIME_TO_EXT
from fastapi import HTTPException
from datetime import timedelta


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
