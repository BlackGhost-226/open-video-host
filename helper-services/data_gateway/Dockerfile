FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    rustc \
    cargo

RUN mkdir /app
WORKDIR /app

EXPOSE 8282

RUN pip install --no-cache-dir fastapi minio uvicorn

COPY ./helper-services/data_gateway .

CMD ["uvicorn", "data_gateway:app", "--host", "0.0.0.0", "--port", "8282"]
