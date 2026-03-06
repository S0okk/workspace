from typing import Annotated, Optional

from fastapi import Depends, FastAPI, HTTPException
from sqlmodel import Field, Session, SQLModel, create_engine, select

############ models


class NoteBase(SQLModel):
    title: str
    text: Optional[str] = None


class Note(NoteBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class NoteCreate(NoteBase):
    pass


class NoteUpdate(NoteBase):
    pass


############ db

engine = create_engine("sqlite:///notes.db", connect_args={"check_same_thread": False})


def get_session():
    with Session(engine) as ss:
        yield ss


SessionDp = Annotated[Session, Depends(get_session)]

############ app

app = FastAPI()


@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)


@app.post("/notes", response_model=Note)
def create_note(data: NoteCreate, ss: SessionDp):
    note = Note(**data.model_dump())
    ss.add(note)
    ss.commit()
    ss.refresh(note)
    return note


@app.get("/notes", response_model=list[Note])
def get_notes(ss: SessionDp):
    return ss.exec(select(Note)).all()


@app.get("/notes/{note_id}", response_model=Note)
def get_note(note_id: int, ss: SessionDp):
    note = ss.get(Note, note_id)
    if not note:
        raise HTTPException(404, "Note not found")
    return note


@app.put("/notes/{note_id}", response_model=Note)
def update_note(note_id: int, data: NoteUpdate, ss: SessionDp):
    note = ss.get(Note, note_id)
    if not note:
        raise HTTPException(404, "Note not found")
    updates = data.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(400, "No data to update")
    for key, value in updates.items():
        setattr(note, key, value)

    ss.commit()
    ss.refresh(note)
    return note


@app.delete("/notes/{note_id}", response_model=dict)
def delete_note(note_id: int, ss: SessionDp):
    note = ss.get(Note, note_id)
    if not note:
        raise HTTPException(404, "Note not found")
    ss.delete(note)
    ss.commit()
    return {"status": "ok"}
