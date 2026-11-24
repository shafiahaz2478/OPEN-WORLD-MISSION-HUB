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


DB_PATH = "./app/data/missions.db"
engine = create_engine(f"sqlite:///{DB_PATH}")

Base = declarative_base()

class Users(Base):
    __tablename__ = "Users"
    user_id = Column(Integer, primary_key=True)
    user_name = Column(String)
    password = Column(String)
    user_role = Column(String, default ="player")

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

