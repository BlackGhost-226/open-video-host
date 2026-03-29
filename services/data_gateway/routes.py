from . import app
from . import minio_client
from . import UPLOAD_BUCKET
from . import OUTPUT_BUCKET
from . import MIME_TO_EXT

from . import Session
from sqlalchemy import select
from sqlalchemy import insert
from sqlalchemy.exc import ProgrammingError
from .posts import create_row_POST
from models import Video

from fastapi import HTTPException
from fastapi.responses import StreamingResponse
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

        fmt = MIME_TO_EXT.get(stat.content_type)

        return {
            "bucket": bucket,
            "object": object_name,
            "download_url": url,
            "format": fmt
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/minio/delete-object")
def delete_object(bucket: str, object_name: str):
    """
    Deletes an object from MinIO.
    """
    objects_to_delete = minio_client.list_objects(bucket, prefix=object_name, recursive=True)
    objects_to_delete = [x.object_name for x in objects_to_delete]
    for object in objects_to_delete:
        minio_client.remove_object(bucket, object)
    return {
        "bucket": bucket,
        "object": object_name
    }

@app.get("/stream/{video_id}/{format_type}/{filename}")
def stream(video_id: str, format_type: str, filename: str):
    respones = minio_client.get_object(OUTPUT_BUCKET, f"{video_id}/{format_type}/{filename}")
    return StreamingResponse(respones)


tables = {Video.__tablename__: Video}
@app.get("/db/{table}")
def get_row(table: str, id: str):
    with Session() as session:
        try:
            sql_table = tables[table]
            results = session.execute(select(sql_table).where(sql_table.id == id))
        except ProgrammingError:
            raise HTTPException(404)
        else:
            result_dict = results.mappings().first()
    return result_dict

@app.post("/db/{table}")
def add_row(table: str, post_data: create_row_POST):
    with Session() as session:
        try:
            sql_table = tables[table]
            results = session.execute(insert(sql_table).values(**post_data.kwargs).returning(sql_table))
        except ProgrammingError:
            raise HTTPException(400)
        else:
            result_dict = results.mappings().first()
    return result_dict