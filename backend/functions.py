from sqlalchemy import Integer, String,Float, Column, create_engine, DateTime, ForeignKey, func, Date
from sqlalchemy.orm import Session, declarative_base, session
from datetime import datetime, date, timedelta, timezone
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ACCESS_TOKEN_EXPIRY = 15
REFRESH_TOKEN_EXPIRY = 7 * 24 * 60
SECRET_KEY ="SECRET123"
ALGORITHM = "HS256"

ph = PasswordHasher()


DB_PATH = "./warehouse.db"
engine = create_engine(f"sqlite:///{DB_PATH}")

Base = declarative_base()

class Users(Base):
    __tablename__ = "Users"
    user_id = Column(Integer, primary_key=True)
    user_name = Column(String)
    password = Column(String)
    user_role = Column(String, default ="player")

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
    player_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="accepted")
    completion_details = Column(String)
    accepted_at = Column(DateTime, default=datetime.now)
    submitted_at = Column(DateTime)

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

def register_user(user_name:str,password:str,user_role:str="user"):
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

    player = session.query(User).filter_by(username=username).first()
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
        player_id=player.id,
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
    player = session.query(User).filter_by(username=username).first()
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
