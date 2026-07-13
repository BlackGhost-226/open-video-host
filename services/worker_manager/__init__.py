from fastapi import FastAPI
from fastapi import HTTPException
from pydantic import BaseModel

from pika import DeliveryMode
from pika import BasicProperties
from pika import ConnectionParameters
from pika import BlockingConnection

from clients.data_gateway import GatewayClient

import math
import json

connection = BlockingConnection(
    ConnectionParameters(host='rabbitmq', heartbeat=0))
channel = connection.channel()
channel.queue_declare(queue='task_queue', 
                      durable=True, 
                      arguments={'x-max-priority': 10})

GWClient = GatewayClient()

def size_to_priority(size_bytes, max_priority=10):
    size = max(size_bytes, 1)
    priority = max_priority - int(math.log10(size))
    return max(0, min(max_priority, priority))

class new_job_POST(BaseModel):
    upload_id: str
    size: int
    init_vars: dict
    user_id: str

app = FastAPI()

@app.post('/vid_with_img')
def new_job(post_data: new_job_POST):
    with open("vid_upload_with_img.json", mode="r") as file:
        instructions = json.load(file)

    GWClient.add_row_to_db("video_tasks", 
                           id=post_data.upload_id, 
                           instructions=instructions,
                           init_vars=post_data.init_vars,
                           author_user_id=post_data.user_id
                            )
    
    channel.basic_publish(
        exchange='',
        routing_key='task_queue',
        body=post_data.upload_id,
        properties=BasicProperties(
            delivery_mode=DeliveryMode.Persistent,
            priority=size_to_priority(post_data.size)
        )
    )

@app.post('/vid_without_img')
def new_job(post_data: new_job_POST):
    with open("vid_upload_without_img.json", mode="r") as file:
        instructions = json.load(file)
        
    GWClient.add_row_to_db("video_tasks", 
                           id=post_data.upload_id, 
                           instructions=instructions,
                           init_vars=post_data.init_vars,
                           author_user_id=post_data.user_id
                            )
    
    channel.basic_publish(
        exchange='',
        routing_key='task_queue',
        body=post_data.upload_id,
        properties=BasicProperties(
            delivery_mode=DeliveryMode.Persistent,
            priority=size_to_priority(post_data.size)
        )
    )
