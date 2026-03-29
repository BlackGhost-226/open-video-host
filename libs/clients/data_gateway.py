import requests
from dataclasses import dataclass
from requests import Response
from typing import Any
from json import loads


class ResultRow:
    def __getattr__(self, name: str) -> Any:
        try:
            return self.__dict__[name]
        except KeyError:
            raise AttributeError(name) from None

    def __setattr__(self, name: str, value: Any) -> None:
        self.__dict__[name] = value

    def __delattr__(self, name: str) -> None:
        try:
            del self.__dict__[name]
        except KeyError:
            raise AttributeError(name) from None
    
    def __getitem__(self, name: str) -> Any:
        try:
            return self.__dict__[name]
        except KeyError:
            raise AttributeError(name) from None

    def __setitem__(self, name: str, value: Any) -> None:
        self.__dict__[name] = value

    def __delitem__(self, name: str) -> None:
        try:
            del self.__dict__[name]
        except KeyError:
            raise AttributeError(name) from None

    def get(self, name: str, default: Any | None = None) -> Any:
        return self.__dict__.get(name, default)

    def pop(self, name: str) -> Any:
        return self.__dict__.pop(name)

class GatewayClient:
    def __init__(self):
        self.baseUrl = "http://data_gateway"
        self.minioUrl = self.baseUrl+"/minio"
        self.dbUrl = self.baseUrl+"/db"
    
    def upload_file_to_minio(self, file, object_name: str, bucket: str) -> None:
        upload_url = requests.get(f"{self.minioUrl}/upload-url?object_name={object_name}&bucket={bucket}").json()["upload_url"]
        requests.put(url=upload_url,
                     data=file,
                     #headers={"Content-Type": file.mimetype}
                    )
    
    def download_file_from_minio(self, object_name: str, bucket: str) -> tuple[Response, str]:
        response = requests.get(f"{self.minioUrl}/download-url?object_name={object_name}&bucket={bucket}")
        format = response.json()["format"]
        download_url = response.json()["download_url"]

        return (requests.get(download_url, stream=True), format)
    
    def write_from_stream(self, stream: Response, file_path: str) -> None:
        with open(file_path, "wb") as file:
            for chunk in stream.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
    
    def delete_file_from_minio(self, object_name, bucket) -> None:
        requests.get(f"{self.minioUrl}/delete-object?object_name={object_name}&bucket={bucket}")


    def get_row_from_db(self, id: str, table: str, key: str) -> ResultRow:
        response = requests.get(f"{self.dbUrl}/{table}?id={id}")
        NewRow = ResultRow()
        for key, value in response.json()[key].items():
            NewRow[key] = value
        return NewRow
    
    def edit_row_in_db(self, id: str, table: str, key: str, **fieldsToEdit) -> ResultRow:
        args = str()
        for key, value in fieldsToEdit.items():
            agrs = args + f"{key}={value}&"
        args = args[:-1]

        response = requests.put(f"{self.dbUrl}/{table}?id={id}&{args}")
        
        NewRow = ResultRow()
        for key, value in response.json()[key].items():
            NewRow[key] = value
        return NewRow
    
    def add_row_to_db(self, table: str, key: str, **fieldsToAdd) -> ResultRow:
        response = requests.post(f"{self.dbUrl}/{table}", json={"kwargs": fieldsToAdd})

        NewRow = ResultRow()
        for key, value in response.json()[key].items():
            NewRow[key] = value
        print(NewRow.__dict__)
        return NewRow
