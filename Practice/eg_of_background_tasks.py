from fastapi import FastAPI, BackgroundTasks
import time
import asyncio

app = FastAPI()

def sync_task():
    time.sleep(3)
    print("Отправлен email")

async def async_task():
    time.sleep(3)
    print("Сделан запрос в сторонний API")


@app.post("/")
async def root(bg_tasks: BackgroundTasks):
    ...
    asyncio.create_task(async_task()) # -> асинхроные задачи
    # bg_tasks.add_task(sync_task) # -> синхронные задачи
    return {"status": "success"}