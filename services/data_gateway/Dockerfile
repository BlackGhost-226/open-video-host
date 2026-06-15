FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    rustc \
    cargo

RUN mkdir /app
WORKDIR /app

EXPOSE 80

RUN pip install --no-cache-dir fastapi minio uvicorn sqlalchemy psycopg2-binary python-multipart

COPY ./services/data_gateway ./app

COPY ./libs/models ./models

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "80"]
