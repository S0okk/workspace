from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse, FileResponse

app = FastAPI()

@app.post("/upload")
async def upload_file(uploaded_file: UploadFile):
    file = uploaded_file.file
    filename = uploaded_file.filename
    with open(f"1_{filename}", "wb") as f:
        f.write(file.read())

@app.post("/multiple-upload")
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
@app.get("/files/{file_name}")
async def get_file(file_name: str):
    return FileResponse(file_name)

# Show file as streaming response
@app.get("/stream/{file_name}")
async def stream_file(filename: str):
    return StreamingResponse(iterfile(filename), media_type="text/plain") 