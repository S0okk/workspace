from fastapi import FastAPI
from sqlalchemy import create_engine, table, Column, Integer, String, MetaData, select

create_engine = create_engine('postgresql+psycopg2://nikitasokolov:Yudacha30121981@localhost/notifications_db')

app = FastAPI()

@app.post("/notifications", tags=["Notifications 🔔"])
async def get_notifications():
    