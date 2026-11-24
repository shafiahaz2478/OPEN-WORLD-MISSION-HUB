from datetime import date
from urllib import response

from fastapi import FastAPI, HTTPException, Body, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import functions

app = FastAPI()

app.add_middleware(CORSMiddleware,
                   allow_origins=["http://localhost:5173"],
                   allow_methods=["*"],
                   allow_headers=["*"])

class Users(BaseModel):
    user_name: str
    password : str
    user_role: str

@app.post("/auth/register")
def register_user(user:Users):
    if functions.register_user(user_name=user.user_name,password=user.password,user_role=user.user_role) is True:
        return {"message": "user registered successfully"}
    raise HTTPException(status_code=400,detail="Username already exists")

@app.post("/auth/login")
def login(username = Body(),password = Body()):
    tokens = functions.verify_login(username=username,password=password)
    if not tokens:
        raise HTTPException(status_code=401,detail="Invalid credentials")
    return tokens

@app.post("/auth/refresh")
def refresh(refresh_token):
    payload = functions.verify_token(token=refresh_token,token_type="refresh")
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or Expired Token")
    username= payload.get("username")
    user_role = payload.get("user_role","user")

    access_token = functions.create_token(username=username,token_type="access",user_role=user_role)
    return {"access_token":access_token}


