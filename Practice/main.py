from fastapi import FastAPI, HTTPException
import uvicorn
from pydantic import BaseModel, EmailStr, Field, ConfigDict


app = FastAPI()


books = [
    {
        "id": 1,
        "title": "1984",
        "author": "George Orwell"
    },
    {
        "id": 2,
        "title": "To Kill a Mockingbird",
        "author": "Harper Lee"
    }
]

users = [
    {
        "id": 1,
        "email": "abc@gmail.com",
        "bio": None,
        "age": 11
    }
]


class NewBook(BaseModel):
    id: int
    title: str = Field(max_length=50)
    author: str = Field(max_length=30)
    
    model_config = ConfigDict(extra='forbid')

class UserSchema(BaseModel):
    id: int
    email: EmailStr
    bio: str | None = Field(max_length=1000)
    
    model_config = ConfigDict(extra='forbid')

class UserAgeSchema(UserSchema):
    age: int = Field(ge=0, lt=130)
    
    model_config = ConfigDict(extra='forbid')


@app.get("/users/", tags=["Users"], response_model=list[UserAgeSchema])
def read_users():
    return users

@app.post("/users/", tags=["Users"])
def add_user(user: UserAgeSchema):
    users.append(
        {
        "id": len(users) + 1,
        "email": user.email,
        "bio": user.bio,
        "age": user.age
        }
    )
    return {'success': True, 'message': 'User added successfully'}


@app.get("/books/", tags=["Books"], response_model=list[NewBook])
def read_books():
    return books

@app.get("/books/{book_id}", tags=["Books"])
def get_book(book_id: int):
    for book in books:
        if book["id"] == book_id:
            return book
    raise HTTPException(status_code=404, detail="Book not found")

@app.post("/books/", tags=["Books"])
def create_book(book: NewBook):
    books.append({
        "id": len(books) + 1,
        "title": book.title,
        "author": book.author
    })
    return {'success': True, 'message': 'Book added successfully'}

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)