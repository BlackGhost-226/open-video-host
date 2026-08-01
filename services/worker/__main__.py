import os
import shutil
import json

from pika.spec import BasicProperties
from pika.spec import Basic
from pika.channel import Channel

from utils import working_dir, GWClient, channel, run_fab

def process_video(ch: Channel, method: Basic.Return, properties: BasicProperties, body: bytes):
    row = GWClient.get_row_from_db("video_tasks", id=body.decode())[0]
    upload_id: str = row.get("id")
    instructions: list = row.get("instructions")["intructions"]
    vars: dict = row.get("init_vars")
    os.makedirs(working_dir, exist_ok=True)

    run = run_fab.new_run(vars, {"upload_id": upload_id})
    run.perform(instructions)
    
    # --| remove |--
    GWClient.delete_file_from_minio(upload_id, "uploads")
    GWClient.delete_row_from_db("video_tasks", upload_id)
    shutil.rmtree(working_dir)

    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue='task_queue', on_message_callback=process_video)
channel.start_consuming()
