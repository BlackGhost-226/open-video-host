import pika
import os
import shutil
import ffmpeg_utils
from ffmpeg_utils import compress_file
from json import loads
from clients.data_gateway import GatewayClient

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='rabbitmq'))
channel = connection.channel()
channel.queue_declare(queue='task_queue', 
                      durable=True, 
                      arguments={'x-max-priority': 10})
channel.basic_qos(prefetch_count=1)

working_dir = "working"
working_dir = os.path.join(".", working_dir)
os.mkdir(working_dir)

GWClient = GatewayClient()


def process_video(ch, method, properties, body):
    dict_body = loads(body)
    upload_id = dict_body["upload_id"]
    title = dict_body["title"]
    description = dict_body["description"]
    author_id = dict_body["aid"]
    os.makedirs(working_dir, exist_ok=True)

    response = GWClient.download_file_from_minio(object_name=f"{upload_id}/video", bucket="uploads")
    video_path = os.path.join(working_dir, "video."+response[1])
    GWClient.write_from_stream(response[0], video_path)

    response = GWClient.download_file_from_minio(object_name=f"{upload_id}/thumbnail", bucket="uploads")
    has_img = response[0].status_code == 200
    if has_img:
        img_path = os.path.join(working_dir, "thumbnail."+response[1])
        GWClient.write_from_stream(response[0], img_path)
    
    #logger.info(f"Video file uploaded: {video_path}")

    # Create directories for each format
    hls_output_dir = os.path.join(working_dir, 'hls')
    dash_output_dir = os.path.join(working_dir, 'dash')
    os.makedirs(hls_output_dir, exist_ok=True)
    os.makedirs(dash_output_dir, exist_ok=True)

    compress_file(video_path, ffmpeg_utils.compress_video)
        
    if has_img:
        compress_file(img_path, ffmpeg_utils.compress_img)
        shutil.move(img_path, working_dir+"/thumbnail.jpg")
    else:
        ffmpeg_utils.get_jpg(video_path, working_dir+"/thumbnail.jpg")

    hls_result = ffmpeg_utils.convert_to_hls(video_path, hls_output_dir)
    dash_result = ffmpeg_utils.convert_to_dash(video_path, dash_output_dir)


    # --| adding video to db |--
    video = GWClient.add_row_to_db(table="videos", title=title, description=description, author_user_id=author_id)[0]
    video_id = video.id

    # --| uploads files |--
    # hls
    for filename in os.listdir(hls_output_dir):
        filePath = os.path.join(hls_output_dir, filename)
        with open(filePath, "rb") as fileData:
            GWClient.upload_file_to_minio(fileData, f"{video_id}/hls/{filename}", "streams", content_type="application/x-mpegURL")
    
    # dash
    for filename in os.listdir(dash_output_dir):
        filePath = os.path.join(dash_output_dir, filename)
        with open(filePath, "rb") as fileData:
            GWClient.upload_file_to_minio(fileData, f"{video_id}/dash/{filename}", "streams", content_type="application/dash+xml")
    
    # img
    with open(working_dir+"/thumbnail.jpg", "rb") as imgData:
        GWClient.upload_file_to_minio(imgData, f"{video_id}/thumbnail.jpg", "streams", content_type="image/jpeg")
    
    # --| remove |--
    GWClient.delete_file_from_minio(upload_id, "uploads")

    shutil.rmtree(working_dir)
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue='task_queue', on_message_callback=process_video)
channel.start_consuming()
