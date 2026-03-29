from fastapi import FastAPI
from fastapi import HTTPException
import asyncio
import requests
from async_worker import AsyncWorker

app = FastAPI()
registry = {}
health_thread = AsyncWorker()

@app.get('/register')
def register(service_name, url):
    if registry[service_name] is  None:
        raise HTTPException(404)
    registry[service_name] = url
    health_thread.submit(health_monitor(service_name))
    return service_name

@app.get('/get')
def get(service_name):
    return registry.get(service_name)

async def health_monitor(service_name):
    while True:
        try:
            await requests.get(registry[service_name]+"/health")
            await asyncio.sleep(5)
        except:
            registry.pop(service_name)
            break
