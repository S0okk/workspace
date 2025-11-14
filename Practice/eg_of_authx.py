from fastapi import FastAPI, HTTPException, Response, Depends
from authx import AuthX, AuthXConfig
from pydantic import BaseModel

app = FastAPI()

config = AuthXConfig()
config.JWT_SECRET_KEY = "supersecretkey"
config.JWT_ACCESS_COOKIE_NAME = "my_access_token"
config.JWT_TOKEN_LOCATION = ["cookies"]

security = AuthX(config)

class UserLoginSchema(BaseModel):
    username: str
    password: str


@app.post("/login")
async def login(creds: UserLoginSchema, response: Response):
    if creds.username == "admin" and creds.password == "password":
        token = security.create_access_token(uid="123")
        response.set_cookie(config.JWT_ACCESS_COOKIE_NAME, token)
        return {"access_token": token}
    return HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/protected", dependencies=[Depends(security.access_token_required)])
async def protected():
    return {"data": "This is protected data"}
