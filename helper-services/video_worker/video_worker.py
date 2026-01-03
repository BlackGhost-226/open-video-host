from fastapi import FastAPI, HTTPException
import requests
import os
import shutil
import ffmpeg_utils
from typing import Callable

app = FastAPI()

working_dir = "working"
working_dir = os.path.join(".", working_dir)
os.mkdir(working_dir)

@app.get('/')
def process_video(upload_id: str, has_img: bool, title: str):

    os.makedirs(working_dir, exist_ok=True)


    response = requests.get(f"http://data_gateway:8282/minio/download-url?object_name={upload_id}/video&bucket=uploads")
    format = response.json()["format"]
    download_url = response.json()["download_url"]
    video_path = os.path.join(working_dir, "video."+format)

    response = requests.get(download_url, stream=True)
    with open(video_path, "wb") as file:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                file.write(chunk)
    
    if has_img:
        response = requests.get(f"http://data_gateway:8282/minio/download-url?object_name={upload_id}/thumbnail&bucket=uploads")
        format = response.json()["format"]
        download_url = response.json()["download_url"]
        img_path = os.path.join(working_dir, "thumbnail."+format)

        response = requests.get(download_url, stream=True)
        with open(img_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
    
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

    # Process video asynchronously
    hls_result = ffmpeg_utils.convert_to_hls(video_path, hls_output_dir)
    dash_result = ffmpeg_utils.convert_to_dash(video_path, dash_output_dir)

    response = requests.get(f"http://data_gateway:8282/minio/video-upload?title={title}")
    #shutil.rmtree(working_dir)

def compress_file(file_path: str, compress_func: Callable):
    os.rename(file_path, file_path+".temp")
    com = compress_func(file_path+".temp", file_path)
    if not com:
        return False
    os.remove(file_path+".temp")
    return True
