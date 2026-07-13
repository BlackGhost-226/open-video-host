import os
import shutil
from typing import Callable
from types import ModuleType

from pika.spec import BasicProperties
from pika.spec import Basic
from pika.channel import Channel

from utils import working_dir, GWClient, channel
from utils.var_utils import VarUtils

ffmpeg_utils: ModuleType = __import__('ffmpeg_utils')

def process_video(ch: Channel, method: Basic.Return, properties: BasicProperties, body: bytes):
    row = GWClient.get_row_from_db("video_tasks", id=body.decode())[0]
    upload_id = row.get("id")
    instructions = row.get("instructions")
    vars = VarUtils(row.get("init_vars"))
    os.makedirs(working_dir, exist_ok=True)

    download_instructions: dict = instructions["download"]
    for command in download_instructions:
        for download_minio_path, var_name in command.items():
            response = GWClient.download_file_from_minio(object_name=f"{upload_id}{download_minio_path}", bucket="uploads")
            file_path = os.path.join(working_dir, f"{download_minio_path}.{response[1]}")
            GWClient.write_from_stream(response[0], file_path)
            if var_name is not None:
                vars[var_name] = file_path

    processing_instructions: dict = instructions["processing"]
    for command in processing_instructions:
        for func_name, args in command.items():
            callable: Callable = getattr(ffmpeg_utils, func_name)
            var_args: list = vars.get_var_args(args)
            output_path = callable(*var_args[:-1])
            if var_args[-1] is not None:
                vars[var_args[-1]] = output_path
    
    sql_instructions: dict = instructions["sql"]
    for command in sql_instructions:
        for query_type, args in command.items():
            callable: Callable = GWClient.add_row_to_db if query_type == "new" else GWClient.get_row_from_db
            var_args: list = vars.get_var_args(args)
            output_row = callable(table=var_args[0], **var_args[1])[0]
            if var_args[-1] is not None:
                vars[var_args[-1]] = output_row

    upload_instructions: dict = instructions["upload"]
    for command in upload_instructions:
        for file_path, bucket_minioPath_contentType in command.items():
            file_path = vars.read_variable(file_path)
            bucket_minioPath_contentType = vars.get_var_args(bucket_minioPath_contentType)
            if os.path.isdir(file_path):
                for filename in os.listdir(file_path):
                    filePath = os.path.join(file_path, filename)
                    with open(filePath, "rb") as fileData:
                        GWClient.upload_file_to_minio(fileData, 
                                                      bucket_minioPath_contentType[1]+f"/{filename}", 
                                                      bucket_minioPath_contentType[0], 
                                                      content_type=bucket_minioPath_contentType[2])
            else:
                with open(file_path, "rb") as fileData:
                    GWClient.upload_file_to_minio(fileData, 
                                                bucket_minioPath_contentType[1], 
                                                bucket_minioPath_contentType[0], 
                                                content_type=bucket_minioPath_contentType[2])
    
    # --| remove |--
    GWClient.delete_file_from_minio(upload_id, "uploads")
    GWClient.delete_row_from_db("video_tasks", upload_id)
    shutil.rmtree(working_dir)

    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue='task_queue', on_message_callback=process_video)
channel.start_consuming()
