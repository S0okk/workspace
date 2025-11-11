from typing import Annotated
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, select

app = FastAPI()

engine = create_async_engine('sqlite+aiosqlite:///books.db')

new_session = async_sessionmaker(engine, expire_on_commit=False)

async def get_session():
    async with new_session() as sessionDp:
        yield sessionDp

class Base(DeclarativeBase):
    pass

class BookModel(Base):
    __tablename__ = 'books'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    author = Column(String, index=True)

class BookAddSchema(BaseModel):
    title: str
    author: str

class BookSchema(BookAddSchema):
    id: int


@app.post("/setup-database", tags=["Database"])
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    return {"message": "Database setup complete."}

@app.delete("/teardown-database", tags=["Database"])
async def teardown_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    return {"message": "Database teardown complete."}

SessionDependency = Annotated[AsyncSession, Depends(get_session)]


@app.post("/books/", tags=["Books"])
async def add_book(data: BookAddSchema, sessionDp: SessionDependency):
    new_book = BookModel(
        title=data.title, 
        author=data.author
        )
    sessionDp.add(new_book)
    await sessionDp.commit()
    return {"Success": True}

@app.get("/books/", response_model=list[BookSchema], tags=["Books"])
async def get_book(sessionDp: SessionDependency):
    query = select(BookModel)
    result = await sessionDp.execute(query)
    return result.scalars().all()
