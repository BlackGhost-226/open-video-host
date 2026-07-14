from . import app
from . import minio_client
from . import UPLOAD_BUCKET
from . import OUTPUT_BUCKET
from . import PROFILE_BUCKET
from . import MIME_TO_EXT

from fastapi import HTTPException
from fastapi import Request
from fastapi import Header
from fastapi.responses import StreamingResponse

from typing import Optional
import asyncio
from .utlis import AsyncStreamIterator


@app.put("/minio/{bucket}/{object_name:path}")
async def upload_stream(object_name: str,
                  request: Request,
                  bucket: str = UPLOAD_BUCKET,
                  content_type: Optional[str] = Header(None)):
    
    if not content_type:
        content_type = "application/octet-stream"
    
    loop = asyncio.get_running_loop()
    async_stream = request.stream()
    stream_bridge = AsyncStreamIterator(async_stream, loop)

    await asyncio.to_thread(minio_client.put_object,
            bucket_name=bucket,
            object_name=object_name,
            data=stream_bridge,
            length=-1,
            part_size=10*1024*1024,
            content_type=content_type)

    return {
        "bucket": bucket,
        "object": object_name
    }

@app.get("/minio/{bucket}/{object_name:path}")
def download_stream(object_name: str, bucket: str = OUTPUT_BUCKET):
    stat = minio_client.stat_object(bucket, object_name)
    fmt = MIME_TO_EXT.get(stat.content_type)
    respones = minio_client.get_object(bucket_name=bucket, object_name=object_name)
    headers = {"Content-Type": stat.content_type, "Format": fmt}
    return StreamingResponse(content=respones, headers={key: str(value) for key, value in headers.items() if value is not None})

@app.delete("/minio/{bucket}/{object_name:path}")
def delete_object(bucket: str, object_name: str):
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
    The same as /minio/download but without permissions and works only with 'OUTPUT_BUCKET' # TODO permissions
    """
    respones = minio_client.get_object(OUTPUT_BUCKET, f"{video_id}/{file_path}")
    return StreamingResponse(respones)

@app.get("/profile/{user_id}")
def profile_img(user_id: str):
    respones = minio_client.get_object(PROFILE_BUCKET, f"{user_id}.jpg")
    return StreamingResponse(respones)
