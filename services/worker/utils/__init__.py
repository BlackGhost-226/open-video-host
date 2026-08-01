from clients.data_gateway import GatewayClient
import pika
from json_lang import LibReg


connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='rabbitmq'))
channel = connection.channel()
channel.queue_declare(queue='task_queue', 
                      durable=True, 
                      arguments={'x-max-priority': 10})
channel.basic_qos(prefetch_count=1)

working_dir = "/app/working"

GWClient = GatewayClient()

from .libs.ffmpeg import ffmpeg_lib
from .libs.s3 import S3_lib
from .libs.sql import sql_lib
run_fab = LibReg()
run_fab.add_lib(ffmpeg_lib)
run_fab.add_lib(S3_lib)
run_fab.add_lib(sql_lib)
