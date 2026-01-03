from app import logger
import os
import json
from flask import jsonify
import shutil
import app.ffmpeg_helper as ffmpeg_helper
import app.utils as utils


def process_video(stream_output_dir, video_upload_dir, video_path, has_img, img_path, data):
            logger.info(f"Video file uploaded: {video_path}")

            # Create directories for each format
            hls_output_dir = os.path.join(stream_output_dir, 'hls')
            dash_output_dir = os.path.join(stream_output_dir, 'dash')
            data_dir = os.path.join(stream_output_dir, 'data')
            os.makedirs(hls_output_dir, exist_ok=True)
            os.makedirs(dash_output_dir, exist_ok=True)
            os.makedirs(data_dir, exist_ok=True)

            json_str = json.dumps(data, indent=4)
            with open(data_dir+"/data.json", "w") as f:
                f.write(json_str)

            if not utils.compress_file(video_path, ffmpeg_helper.compress_video):
                return jsonify({"error:": "cannot compress video"}), 400
        
            if has_img:
                if not utils.compress_file(img_path, ffmpeg_helper.compress_img):
                    return jsonify({"error:": "cannot compress img"}), 400
                shutil.move(img_path, data_dir+"/thumbnail.jpg")
            else:
                if not ffmpeg_helper.get_jpg(video_path, data_dir+"/thumbnail.jpg"):
                    return jsonify({"error:": "cannot extract img"}), 400
                logger.info(f"Img extracted")

            # Process video asynchronously
            hls_result = ffmpeg_helper.convert_to_hls(video_path, hls_output_dir)
            dash_result = ffmpeg_helper.convert_to_dash(video_path, dash_output_dir)
            shutil.rmtree(video_upload_dir)

            #return hls_result and dash_result
