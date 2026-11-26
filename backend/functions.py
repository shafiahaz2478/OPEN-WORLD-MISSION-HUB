from sqlalchemy import Integer, String, Float, Column, create_engine, DateTime, ForeignKey, func, Date, Boolean
from sqlalchemy.orm import Session, declarative_base, session
from datetime import datetime, date, timedelta, timezone
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ACCESS_TOKEN_EXPIRY = 15
REFRESH_TOKEN_EXPIRY = 7 * 24 * 60
SECRET_KEY ="THEBIGSECRETKEYBECAUSEOLDONEISTOOSHORT"
ALGORITHM = "HS256"

ph = PasswordHasher()

#use this path only when testing in swagger
#DB_PATH = "missions.db"
#real path for docker
DB_PATH = "/app/data/missions.db"
engine = create_engine(f"sqlite:///{DB_PATH}")

Base = declarative_base()

class Users(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True)
    user_name = Column(String)
    password = Column(String)
    user_role = Column(String, default ="player")
    rewards = Column(Integer)

class Mission(Base):
    __tablename__ = "missions"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(String)
    difficulty = Column(String)
    location = Column(String)
    xp_reward = Column(Integer)
    is_active = Column(Boolean)


class MissionAcceptance(Base):
    __tablename__ = "mission_acceptances"
    id = Column(Integer, primary_key=True)
    mission_id = Column(Integer, ForeignKey("missions.id"))
    player_id = Column(Integer, ForeignKey("users.user_id"))
    status = Column(String, default="accepted")
    completion_details = Column(String)
    accepted_at = Column(DateTime, default=datetime.now)
    submitted_at = Column(DateTime)

class Rewards(Base):
    __tablename__ = "rewards"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    mission_id = Column(Integer, ForeignKey("missions.id"))
    xp = Column(Integer)
    assigned_to = Column(Integer, ForeignKey("users.user_id") , nullable=True)
    available = Column(Boolean, default=True)

Base.metadata.create_all(engine)


def verify_login(username, password):
    session = Session(engine)
    user = session.query(Users).filter_by(user_name = username).first()
    if user is None:
        session.close()
        return False
    try:
        ph.verify(user.password,password)
    except VerifyMismatchError:
        session.close()
        return False
    if user.user_role:
        user_role = user.user_role
    else:
        user_role = "user"
    session.close()
    access_token = create_token(username=username, token_type="access",user_role=user_role)
    refresh_token = create_token(username=username, token_type="refresh",user_role=user_role)
    return {"access_token": access_token, "refresh_token": refresh_token}

def create_token(username, token_type,user_role="user"):
    payload = {
        "username": username,
        'token_type': token_type,
        'user_role': user_role,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRY if token_type == "access" else REFRESH_TOKEN_EXPIRY)  # turnery expression
    }
    token = jwt.encode(payload=payload, key=SECRET_KEY, algorithm=ALGORITHM)
    return token



def verify_token(token,token_type):
    try:
        payload = jwt.decode(jwt=token, key=SECRET_KEY, algorithms=[ALGORITHM])
    except:
        return False
    if payload["token_type"] == token_type:
        return payload
    return False


#--------- Users -----------

def register_user(user_name:str,password:str,user_role:str="player"):
    session = Session(engine)
    user_exists = session.query(Users).filter_by(user_name=user_name).first()
    if user_exists is not None:
        session.close()
        return False
    session.add(Users(user_name=user_name,password=ph.hash(password),user_role=user_role))
    session.commit()
    session.close()
    return True

def accept_mission(username, mission_id):
    session = Session(engine)
    mission = session.get(Mission, mission_id)
    if mission is None:
        session.close()
        return "not_found"

    if not mission.is_active:
        session.close()
        return "inactive"

    player = session.query(Users).filter_by(username=username).first()
    if player is None:
        session.close()
        return "not_found"

    existing_active = (
        session.query(MissionAcceptance)
        .filter_by(mission_id=mission_id, player_id=player.id, status="accepted")
        .first()
    )
    if existing_active is not None:
        session.close()
        return "already_accepted"

    acceptance = MissionAcceptance(
        mission_id=mission_id,
        player_id=player.user_id,
        status="accepted",
    )
    session.add(acceptance)
    session.commit()

    response = {
        "acceptance_id": acceptance.id,
        "mission_id": acceptance.mission_id,
        "player_id": acceptance.player_id,
        "status": acceptance.status,
        "accepted_at": acceptance.accepted_at,
    }
    session.close()
    return response


def submit_mission(username, mission_id, completion_details):
    session = Session(engine)
    player = session.query(Users).filter_by(username=username).first()
    if player is None:
        session.close()
        return "not_accepted"

    acceptance = (
        session.query(MissionAcceptance)
        .filter_by(mission_id=mission_id, player_id=player.id)
        .order_by(MissionAcceptance.id.desc())
        .first()
    )
    if acceptance is None:
        session.close()
        return "not_accepted"

    if acceptance.status != "accepted":
        session.close()
        return "already_submitted"

    acceptance.completion_details = completion_details
    acceptance.status = "submitted"
    acceptance.submitted_at = datetime.now()
    session.commit()

    response = {
        "acceptance_id": acceptance.id,
        "mission_id": acceptance.mission_id,
        "status": acceptance.status,
        "completion_details": acceptance.completion_details,
        "submitted_at": acceptance.submitted_at,
    }
    session.close()
    return response

def create_rewards(name,mission_id):
    session = Session(engine)
    mission = session.get(Mission , mission_id)
    if not mission_id:
        return {"code":404 , "msg":"Mission not found"}
    xp = difficulty_to_xp(mission.difficulty)


    reward = Rewards(name=name , mission_id = mission_id , xp = xp)
    session.add(reward)
    session.commit()
    response = rewards_to_dict(reward)
    session.close()
    return {"code":200, "reward":response}

def view_all_rewards():
    session = Session(engine)
    rewards = session.query(Rewards).filter(Rewards.available == True).all()
    responses = []
    for reward in rewards:
        responses.append(rewards_to_dict(reward))
    session.close()
    return {"code":200, "rewards":responses}

def assign_rewards(reward_id , user_id):
    session = Session(engine)
    reward = session.get(Rewards, reward_id)
    if not reward:
        return {"code":404 , "msg":"Reward not found"}

    user = session.get(Users, user_id)
    if not user:
        return {"code":404 , "msg":"User not found"}

    user.rewards += reward.xp

    reward.assigned_to = user_id
    session.commit()
    response = rewards_to_dict(reward)
    session.close()
    return {"code":200, "leaderboard":response}

def get_player_rankings(length):
    session = Session(engine)
    players = session.query(Users).filter(Users.user_role == "player").order_by(Users.rewards.desc()).limit(length).all()

    response = []
    i = 1
    for player in players:
        response.append({
            "rank": i,
            "name" : player.user_name,
            "xp": player.rewards
        })
        i += 1

    session.close()
    return {"code":200, "rewards":response}







def rewards_to_dict(rewards : Rewards):
    return {
        "id" : rewards.id,
        "name" : rewards.name,
        "mission_id" : rewards.mission_id,
        "xp" : rewards.xp,
        "assigned_to" : rewards.assigned_to
    }

def difficulty_to_xp(difficulty : str):
    difficulty_to_xp_map = {"easy":50 , "medium":100 , "hard":200, "special":500}
    return difficulty_to_xp_map[difficulty.lower()]

def create_mission_manager(user_name:str,password:str): #E1
    session = Session(engine)
    user_exists = session.query(Users).filter_by(user_name=user_name).first()
    if user_exists is not None:
        session.close()
        return {"code":400 , "msg":"User already exists"}
    mission_manager = Users(user_name=user_name,password=ph.hash(password),user_role="mission_manager")
    session.add(mission_manager)
    session.commit()
    session.close()
    return {"code":200 , "msg":"Mission Manager Account created"}


def mission_to_dict(mission: Mission): #helper func for getting response in E2
    return {
        "id": mission.id,
        "title": mission.title,
        "description": mission.description,
        "difficulty": mission.difficulty,
        "location": mission.location,
        "xp_reward": mission.xp_reward,
        "is_active": mission.is_active
    }

def create_mission(title: str, description: str, difficulty: str, location: str, is_active: bool = True): #E2
    session = Session(engine)
    valid_difficulties = ["easy", "medium", "hard", "special"]
    difficulty = difficulty.lower()
    if difficulty not in valid_difficulties:
        return {"code": 400, "msg": "Invalid difficulty. Must be easy, medium, hard, or special"}
    xp_reward = difficulty_to_xp(difficulty)

    new_mission = Mission(
        title=title,
        description=description,
        difficulty=difficulty,
        location=location,
        xp_reward=xp_reward,
        is_active=is_active
    )
    session.add(new_mission)
    session.commit()
    response = mission_to_dict(new_mission)
    session.close()
    return {"code":200,"mission":response}