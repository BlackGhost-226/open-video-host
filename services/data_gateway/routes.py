from . import app
from . import minio_client
from . import UPLOAD_BUCKET
from . import OUTPUT_BUCKET
from . import MIME_TO_EXT

from . import Session
from sqlalchemy import select
from sqlalchemy import insert
from .posts import create_row_POST
from models import Video
from typing import Optional

from fastapi import HTTPException
from fastapi import Request
from fastapi.responses import StreamingResponse
from io import BytesIO


@app.put("/minio/{bucket}/{object_name:path}")
async def upload_stream(object_name: str, request: Request, bucket: str = UPLOAD_BUCKET):
    buffer = BytesIO()

    async for chunk in request.stream():
        buffer.write(chunk)

    buffer.seek(0)

    minio_client.put_object(
        bucket_name=bucket,
        object_name=object_name,
        data=buffer,
        length=buffer.getbuffer().nbytes)
    return {
        "bucket": bucket,
        "object": object_name
    }

@app.get("/minio/{bucket}/{object_name:path}")
async def download_stream(object_name: str, bucket: str = OUTPUT_BUCKET):
    stat = minio_client.stat_object(bucket, object_name)
    fmt = MIME_TO_EXT.get(stat.content_type)
    respones = minio_client.get_object(bucket_name=bucket, object_name=object_name)
    return StreamingResponse(content=respones, 
                             headers={"Content-Type": stat.content_type, 
                                      "format": fmt})

@app.delete("/minio/{bucket}/{object_name:path}")
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

@app.get("/stream/{video_id}/{file_path:path}")
def stream(video_id: str, file_path: str):
    """
    The same as /minio/download but without permissions and works only with 'OUTPUT_BUCKET'
    """
    respones = minio_client.get_object(OUTPUT_BUCKET, f"{video_id}/{file_path}")
    return StreamingResponse(respones)


tables = {Video.__tablename__: Video}
@app.get("/db/{table}")
def get_row(table: str, id: Optional[str] = None):
    with Session() as session:
        sql_table = tables.get(table)
        if not sql_table:
            raise HTTPException(status_code=404, detail="Table not found")
        if id:
            results = session.execute(select(*sql_table.__table__.c).where(sql_table.id == id))
        else:
            results = session.execute(select(*sql_table.__table__.c))
        result_list = results.mappings().all()
    return {"list": result_list}

@app.post("/db/{table}")
def add_row(table: str, post_data: create_row_POST):
    with Session() as session:
        sql_table = tables.get(table)
        if not sql_table:
            raise HTTPException(status_code=404, detail="Table not found")
        results = session.execute(insert(sql_table).values(**post_data.kwargs).returning(*sql_table.__table__.c))
        result_list = results.mappings().all()
        session.commit()
    return {"list": result_list}