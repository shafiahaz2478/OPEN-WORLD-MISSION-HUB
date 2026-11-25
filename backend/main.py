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

class SubmissionCreate(BaseModel):
    completion_details: str

class SubmissionReview(BaseModel):
    status: str

class CreateReward(BaseModel):
    name : str
    mission_id : int
class CreateMissionManager(BaseModel):
    user_name:str
    password:str


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

@app.post("/missions/{mission_id}/accept")
def accept_mission(mission_id: int, token=Header(None)):
    user = functions.verify_token(token=token, token_type="access")
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    if user["role"] != "player":
        raise HTTPException(status_code=403, detail="Only players can accept missions")
    result = functions.accept_mission(username=user["username"], mission_id=mission_id)
    if result == "not_found":
        raise HTTPException(status_code=404, detail="Mission not found")
    if result == "inactive":
        raise HTTPException(status_code=400, detail="Mission is not active")
    if result == "already_accepted":
        raise HTTPException(status_code=400, detail="Mission already accepted")
    return result

@app.post("/missions/{mission_id}/submit")
def submit_mission(mission_id: int, body: SubmissionCreate, token=Header(None)):
    user = functions.verify_token(token=token, token_type="access")
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    if user["role"] != "player":
        raise HTTPException(status_code=403, detail="Only players can submit mission completion")
    result = functions.submit_mission(
        username=user["username"],
        mission_id=mission_id,
        completion_details=body.completion_details,
    )
    if result == "not_accepted":
        raise HTTPException(status_code=400, detail="Mission has not been accepted")
    if result == "already_submitted":
        raise HTTPException(status_code=400, detail="Mission already submitted or completed")
    return result

@app.post("/rewards")
def create_rewards(reward : CreateReward,token=Header(None)):
    user = functions.verify_token(token=token, token_type="access")
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    if user["role"] != "mission manager":
        raise HTTPException(status_code=403, detail="Only Mission manager can create rewards")

    result = functions.create_rewards(reward.name,reward.mission_id)
    if result["code"] == 200:
        return result["reward"]
    raise HTTPException(status_code=result["code"], detail=result["msg"])


@app.get("/rewards")
def create_rewards(token=Header(None)):
    user = functions.verify_token(token=token, token_type="access")
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    result = functions.view_all_rewards()
    if result["code"] == 200:
        return result["rewards"]
    raise HTTPException(status_code=result["code"], detail=result["msg"])

@app.patch("/rewards/{reward_id}")
def assign_reward(reward_id: int , user_id : int , token=Header(None)):
    user = functions.verify_token(token=token, token_type="access")
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    if user["role"] != "mission manager":
        raise HTTPException(status_code=403, detail="Only Mission manager can create rewards")
    result = functions.create_rewards(reward_id, user_id)
    if result["code"] == 200:
        return result["reward"]
    raise HTTPException(status_code=result["code"], detail=result["msg"])

@app.post("/admin/mission-managers")
def register_mission_manager(mission_manager:CreateMissionManager,token:str = Header(None)):
    user=functions.verify_token(token=token,token_type="access")
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    if user["user_role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create mission manager accounts")
    response = functions.create_mission_manager(user_name=mission_manager.user_name,password=mission_manager.password)

    if response["code"] == 201:
        return {"message":response["msg"]}
    raise HTTPException(status_code=response["code"], detail=response["msg"])