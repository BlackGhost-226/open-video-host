FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    curl \
    rustc \
    cargo

RUN mkdir /app
WORKDIR /app

EXPOSE 80

RUN pip install --no-cache-dir pika requests

COPY ./services/worker ./app
COPY ./libs/clients ./app/clients

CMD ["python", "app"]
