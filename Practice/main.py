from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse, FileResponse
import os

app = FastAPI()

@app.post("/upload", tags=["Files"])
async def upload_file(uploaded_file: UploadFile):
    file = uploaded_file.file
    filename = uploaded_file.filename
    with open(f"1_{filename}", "wb") as f:
        f.write(file.read())

@app.post("/multiple-upload", tags=["Files"])
async def multiple_upload_file(uploaded_files: list[UploadFile]):
    for uploaded_file in uploaded_files:
        file = uploaded_file.file
        filename = uploaded_file.filename
        with open(f"1_{filename}", "wb") as f:
            f.write(file.read())

def iterfile(filename: str):
    with open(filename, "rb") as f:
        while chunk := f.read(1024 * 1024):
            yield chunk



# Show file on local storage
@app.get("/files/{file_name}", tags=["Files"])
async def get_file(filename: str):
    return FileResponse(filename)

# Show file as streaming response
@app.get("/files/stream/{file_name}", tags=["Files"])
async def stream_file(filename: str):
    return StreamingResponse(iterfile(filename), media_type="text/plain")

# Create file
@app.post("/files", tags=["Files"])
async def create_file(filename: str, text: str):
    with open(f"{filename}", "w") as f:
        f.write(text)
    return {"status": "success"}

# Show all files in the sys
@app.get("/files", tags=["Files"])
async def get_files():
    files_in_sys = os.listdir()
    return {"Files in system": files_in_sys}