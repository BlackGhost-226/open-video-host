from json_lang import Lib
from json_lang import RunningEnv
import os
from .. import GWClient
from .. import working_dir

S3_lib = Lib("s3")

@S3_lib.add_func
def upload(file_path: str, bucket: str, minioPath: str, contentType: str):
    if os.path.isdir(file_path):
        for filename in os.listdir(file_path):
            filePath = os.path.join(file_path, filename)
            with open(filePath, "rb") as fileData:
                GWClient.upload_file_to_minio(fileData, 
                                              minioPath+f"/{filename}", 
                                              bucket, 
                                              content_type=contentType)
    else:
        with open(file_path, "rb") as fileData:
            GWClient.upload_file_to_minio(fileData, 
                                        minioPath, 
                                        bucket, 
                                        content_type=contentType)

@S3_lib.add_func
def download(run_env: RunningEnv, minioPath: str):
    response = GWClient.download_file_from_minio(object_name=f"{run_env.lib_only_vars["upload_id"]}{minioPath}", bucket="uploads")
    file_path = os.path.join(working_dir, f"{minioPath.lstrip('/')}.{response[1]}")
    GWClient.write_from_stream(response[0], file_path)
    return file_path
