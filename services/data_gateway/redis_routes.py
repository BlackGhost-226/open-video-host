from . import app
from . import redis_client

from fastapi import HTTPException

@app.get("/redis/{key}")
def get_from_key(key: str):
    value = redis_client.get(key)
    if value is None:
        raise HTTPException(status_code=404, detail="Key not found")
    return value

@app.put("/redis/{key}")
def assign_value_to_key(key: str, value: str):
    redis_client.set(key, value)