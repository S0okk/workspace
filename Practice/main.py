from typing import Annotated
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, select, update

app = FastAPI()

engine = create_async_engine('sqlite+aiosqlite:///books.db')

new_session = async_sessionmaker(engine, expire_on_commit=False)

async def get_session():
    async with new_session() as session:
        yield session

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
    
    class Config:
        from_attributes = True


@app.post("/setup-database", tags=["Database 🗃️"], description="This endpoint creates a new setup for database")
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    return {"message": "Database setup complete."}

@app.delete("/drop-database", tags=["Database 🗃️"], description="This endpoint drops a database")
async def drop_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    return {"message": "Database was dropped successfully."}

SessionDependency = Annotated[AsyncSession, Depends(get_session)]


@app.post("/books/", tags=["Books 📚"], description="This endpoint adds a book in the database")
async def add_book(data: BookAddSchema, session: SessionDependency):
    new_book = BookModel(
        title=data.title, 
        author=data.author
        )
    session.add(new_book)
    await session.commit()
    return {"Success": True}

@app.get("/books/", response_model=list[BookSchema], tags=["Books 📚"], description="This endpoint shows all books in the database")
async def show_books(session: SessionDependency):
    query = select(BookModel)
    result = await session.execute(query)
    return result.scalars().all()

@app.get("/books/{book_id}", response_model=BookSchema, tags=["Books 📚"], description="This endpoint finds a book in the database")
async def get_book(book_id: int, session: SessionDependency):
    query = select(BookModel).where(BookModel.id == book_id)
    result = await session.execute(query)
    return result.scalars().first()

@app.put("/books/{book_id}", tags=["Books 📚"], description="This endpoint updates a book in the database")
async def update_book(data: BookAddSchema, book_id: int, session: SessionDependency):
    from sqlalchemy import update
    result = (
        update(BookModel)
        .where(BookModel.id == book_id)
        .values(title=data.title, author=data.author)
    )
    await session.execute(result)
    await session.commit()
    return {"Success": True}
