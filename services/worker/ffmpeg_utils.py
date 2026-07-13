import subprocess
import os
from typing import Callable
from utils import working_dir


def compress_file(input_path: str, type: str):
    compress_func: Callable = compress_video if type == "video" else compress_img
    os.rename(input_path, input_path+".temp")
    com = compress_func(input_path+".temp", input_path)
    if not com:
        return False
    os.remove(input_path+".temp")
    return com

def convert_to_hls(input_path: str, type: str):
    """Convert video to HLS format using FFmpeg"""
    output_dir = os.path.join(working_dir, 'hls')
    os.makedirs(output_dir, exist_ok=True)

    hls_playlist = os.path.join(output_dir, 'playlist.m3u8')

    # HLS conversion command
    hls_cmd = [
        'ffmpeg', '-i', input_path,
        '-profile:v', 'baseline',
        '-level', '3.0',
        '-start_number', '0',
        '-hls_time', '10',
        '-hls_list_size', '0',
        '-f', 'hls',
        hls_playlist
    ]

    try:
        subprocess.run(hls_cmd, check=True)
        #logger.info(f"HLS conversion completed for {input_path}")
        return output_dir
    except subprocess.CalledProcessError as e:
        #logger.error(f"HLS conversion failed: {e}")
        return False

def convert_to_dash(input_path: str, type: str):
    """Convert video to DASH format using FFmpeg"""
    output_dir = os.path.join(working_dir, 'dash')
    os.makedirs(output_dir, exist_ok=True)

    dash_playlist = os.path.join(output_dir, 'manifest.mpd')

    # DASH conversion command
    dash_cmd = [
        'ffmpeg', '-i', input_path,
        '-map', '0:v?', '-map', '0:a?',
        '-c:v', 'libx264', '-x264-params', 'keyint=60:min-keyint=60:no-scenecut=1',
        '-b:v:0', '1500k',
        '-c:a', 'aac', '-b:a', '128k',
        '-bf', '1', '-keyint_min', '60',
        '-g', '60', '-sc_threshold', '0',
        '-f', 'dash',
        '-use_template', '1', '-use_timeline', '1',
        '-init_seg_name', 'init-$RepresentationID$.m4s',
        '-media_seg_name', 'chunk-$RepresentationID$-$Number%05d$.m4s',
        '-adaptation_sets', 'id=0,streams=v id=1,streams=a',
        dash_playlist
    ]

    try:
        subprocess.run(dash_cmd, check=True)
        #logger.info(f"DASH conversion completed for {input_path}")
        return output_dir
    except subprocess.CalledProcessError as e:
        #logger.error(f"DASH conversion failed: {e}")
        return False

def compress_video(input_path: str, output_path: str):
    compress_cmd = ["ffmpeg", "-i", input_path, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "25", 
                    "-preset", "fast", "-tune", "zerolatency", "-c:a", "aac", output_path]
    
    try:
        subprocess.run(compress_cmd, check=True)
        #logger.info(f"{input_path} had been compressed")
        return True
    except subprocess.CalledProcessError as e:
        #logger.error(f"compression failed: {e}")
        return False

def compress_img(input_path: str, output_path: str):
    compress_cmd = ['ffmpeg',
                    '-i', input_path,
                    '-q:v', '2',
                    '-vf',
                    "scale=if(gte(a\\,16/9)\\,iw\\,-1):if(lt(a\\,16/9)\\,-1\\,ih),"
                    "pad=ceil(max(iw\\,ih*16/9)/2)*2:ceil(max(ih\\,iw*9/16)/2)*2:"
                    "(ow-iw)/2:(oh-ih)/2:black",
                    output_path]

    try:
        subprocess.run(compress_cmd, check=True)
        #logger.info(f"{input_path} had been compressed")
        return True
    except subprocess.CalledProcessError as e:
        #logger.error(f"compression failed: {e}")
        return False

def get_jpg(input_path: str, type: str):
    output_path = os.path.join(working_dir, f"{input_path.split("/")[-1].split(".")[0]}.jpg")
    jpg_cmd = ['ffmpeg',
               '-ss', '00:00:02',
               '-i', input_path,
               '-vframes', '1',
               '-q:v', '2',
               '-vf',
                "scale=if(gte(a\\,16/9)\\,iw\\,-1):if(lt(a\\,16/9)\\,-1\\,ih),"
                "pad=ceil(max(iw\\,ih*16/9)/2)*2:ceil(max(ih\\,iw*9/16)/2)*2:"
                "(ow-iw)/2:(oh-ih)/2:black",
               output_path]

    try:
        subprocess.run(jpg_cmd, check=True)
        #logger.info(f"{output_path} had been extracted")
        return output_path
    except subprocess.CalledProcessError as e:
        #logger.error(f"extraction failed: {e}")
        return False

def set_scale(input_path: str, type: str):
    pass
