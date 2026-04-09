import requests
from dataclasses import dataclass
from requests import Response
from typing import Any, Optional
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

        self.chunk_size = 64*1024
    
    def upload_file_to_minio(self, file, object_name: str, bucket: str, content_type: Optional[str] = None) -> None:
        requests.put(f"{self.minioUrl}/{bucket}/{object_name}",
                    data=self.file_chunker(file),
                    headers={"Content-Type": content_type})
    
    def file_chunker(self, file):
        while True:
            chunk = file.read(self.chunk_size)
            if not chunk:
                break
            yield chunk
    
    def download_file_from_minio(self, object_name: str, bucket: str) -> tuple[Response, str]:
        response = requests.get(f"{self.minioUrl}/{bucket}/{object_name}", stream=True)
        format = response.headers.get("format")
        return (response, format)
    
    def write_from_stream(self, stream: Response, file_path: str) -> None:
        with open(file_path, "wb") as file:
            for chunk in stream.iter_content(chunk_size=self.chunk_size):
                if chunk:
                    file.write(chunk)
    
    def delete_file_from_minio(self, object_name, bucket) -> None:
        requests.delete(f"{self.minioUrl}/{bucket}/{object_name}")


    def get_row_from_db(self, table: str, id: str = "") -> list[ResultRow]:
        response = requests.get(f"{self.dbUrl}/{table}?id={id}")

        rows: list[ResultRow] = list()
        rowList: list[dict[str, str]] = response.json()["list"]
        for item in rowList:
            newRow = ResultRow()
            for key, value in item.items():
                newRow[key] = value
            rows.append(newRow)
        return rows
    
    def edit_row_in_db(self, id: str, table: str, **fieldsToEdit) -> ResultRow:
        pass
    
    def add_row_to_db(self, table: str, **fieldsToAdd) -> list[ResultRow]:
        response = requests.post(f"{self.dbUrl}/{table}", json={"kwargs": fieldsToAdd})

        rows: list[ResultRow] = list()
        rowList: list[dict[str, str]] = response.json()["list"]
        for item in rowList:
            newRow = ResultRow()
            for key, value in item.items():
                newRow[key] = value
            rows.append(newRow)
        return rows
