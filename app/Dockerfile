FROM python:3.12.4-alpine3.20

# We need curl for the health check
RUN apk --no-cache add curl

WORKDIR /app

# First, copy dependencies only
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt


COPY app.py .

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
