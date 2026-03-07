FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    curl \
    rustc \
    cargo

RUN mkdir /video_worker
WORKDIR /video_worker

EXPOSE 80

RUN pip install --no-cache-dir fastapi uvicorn requests

COPY ./helper-services/video_worker .

CMD ["uvicorn", "video_worker:app", "--host", "0.0.0.0", "--port", "80"]
