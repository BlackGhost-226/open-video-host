from clients.data_gateway import GatewayClient

import os

import pika


connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='rabbitmq'))
channel = connection.channel()
channel.queue_declare(queue='task_queue', 
                      durable=True, 
                      arguments={'x-max-priority': 10})
channel.basic_qos(prefetch_count=1)

working_dir = "/app/working"

GWClient = GatewayClient()
