from typing import Annotated
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy import DateTime, Column, Integer, String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from datetime import datetime


# engine = create_async_engine('postgresql+asyncpg://nikitasokolov:Yudacha30121981@localhost/notifications_db', future=True)
engine = create_async_engine('postgresql+asyncpg://postgres:Yudacha30121981@localhost/notifications_db', future=True)

new_session = async_sessionmaker(engine, expire_on_commit=False)

async def get_session():
    async with new_session() as session:
        yield session

SessionDependency = Annotated[AsyncSession, Depends(get_session)]


class Base(DeclarativeBase):
    pass

# DB Model
class NotificationModel(Base):
    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True, index=True)
    user = Column(String, index=True)
    message = Column(String, index=True)
    time = Column(DateTime, nullable=False)

# Pydantic schemas
class NotificationAddSchema(BaseModel):
    user: str
    message: str
    time: datetime

class NotificationSchema(NotificationAddSchema):
    id: int


app = FastAPI()


@app.post("/setup-database", tags=["Database 🗃️"], description="This endpoint creates a new setup for database")
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    return {"message": "Database setup complete."}


@app.post("/notifications", tags=["Notifications 🔔"])
async def add_notifications(data: NotificationAddSchema, session: SessionDependency):
    new_notification = NotificationModel(
        user = data.user,
        message = data.message,
        time = data.time
    )
    session.add(new_notification)
    await session.commit()
    return {"Success": True}