FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    rustc \
    cargo

RUN mkdir /app
WORKDIR /app

EXPOSE 80

RUN pip install --no-cache-dir requests fastapi==0.128.0 uvicorn==0.38.0 cryptography==46.0.3 sqlalchemy pyjwt[crypto]==2.10.1 bcrypt==5.0.0 validators==0.35.0 psycopg2-binary==2.9.11

COPY ./services/auth_authority ./auth_authority
COPY ./models/jwt_token ./jwt_token

CMD ["uvicorn", "auth_authority:app", "--host", "0.0.0.0", "--port", "80"]
