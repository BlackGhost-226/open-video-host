FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    rustc \
    cargo

RUN mkdir /data_gateway
WORKDIR /data_gateway

EXPOSE 80

RUN pip install --no-cache-dir fastapi minio uvicorn

COPY ./services/data_gateway .

CMD ["uvicorn", "data_gateway:app", "--host", "0.0.0.0", "--port", "80"]
