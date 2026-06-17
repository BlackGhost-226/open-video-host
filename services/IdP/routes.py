from .posts import login_POST
from .posts import refresh_POST
from .posts import create_user_POST

from . import app
from . import private_key_pem
from . import public_key_pem
from . import Session
from . import redis_client

from . import dumy_password
from . import dumy_password_hash

from jwt_token.token import refreshTokenConfig
from jwt_token.token import accessTokenConfig
import jwt_token.token as token
from jwt_token.token import encode
from jwt_token.token import decode
from uuid import uuid4

from models import User
from models import RefreshToken
from sqlalchemy import select

from fastapi import HTTPException

from bcrypt import checkpw
from bcrypt import hashpw
from bcrypt import gensalt

import validators

from datetime import timedelta

@app.get("/public_key")
async def get_key():
    return {"key": public_key_pem}

@app.post("/login")
async def login(post_data: login_POST):
    with Session() as session:
        user = session.execute(select(User).where(User.email == post_data.email)).scalar_one_or_none()

        if not user:
            checkpw(dumy_password.encode("utf-8"), dumy_password_hash)
            raise HTTPException(401, "Invalid  login credentials")

        if not checkpw(post_data.password.encode("utf-8"), user.password_hash):
            raise HTTPException(401, "Invalid login credentials")

        existing = session.execute(
            select(RefreshToken)
            .where(
                RefreshToken.user_id == user.id,
                RefreshToken.device_agent == post_data.user_agent
            )
        ).scalar_one_or_none()

        if existing:
            session.delete(existing)
            session.flush()

        refresh = RefreshToken(user=user, issuer=refreshTokenConfig.issuer, device_agent=post_data.user_agent)
        session.add(refresh)
        session.flush()

        csrf = str(uuid4().hex)
        access_token = encode(secret=private_key_pem,
                              token=token.AccessToken({"sub": str(user.id), "csrf": csrf, "jti": str(refresh.last_access_jti), "fresh": True}),
                              config=accessTokenConfig)

        refresh_token = encode(secret=private_key_pem,
                              token=token.RefreshToken({"jti": str(refresh.id), "csrf": csrf}),
                              config=refreshTokenConfig)

        session.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "access_exp_seconds": accessTokenConfig.exp_seconds,
            "refresh_exp_seconds": refreshTokenConfig.exp_seconds,
            "csrf": csrf
        }

@app.post("/refresh")
async def refresh(post_data: refresh_POST):
    with Session() as session:
        refresh_token = decode(encoded_token=post_data.refresh_token, secret=public_key_pem, token=token.RefreshToken, config=refreshTokenConfig)
        refresh_token_db = session.execute(select(RefreshToken).where(RefreshToken.id == refresh_token.jwtId)).scalar_one_or_none()

        if refresh_token_db is None:
            raise HTTPException(status_code=404, detail="There is no such refresh token")
        
        if str(refresh_token_db.last_access_jti) == post_data.last_access_jti:
            user = refresh_token_db.user
            user_agent = refresh_token_db.device_agent
            session.delete(refresh_token_db)
            session.flush()

            refresh = RefreshToken(user=user, issuer=refreshTokenConfig.issuer, device_agent=user_agent)
            session.add(refresh)
            session.flush()

            csrf = str(uuid4().hex)
            if post_data.password is not None:
                is_password_correct = checkpw(post_data.password.encode("utf-8"), user.password_hash)
                if is_password_correct:
                    access_token = encode(secret=private_key_pem, 
                                          token=token.AccessToken({"sub": str(user.id), "csrf": csrf, "jti": str(refresh.last_access_jti), "fresh": True}), 
                                          config=accessTokenConfig)
                else:
                    access_token = encode(secret=private_key_pem, 
                                          token=token.AccessToken({"sub": str(user.id), "csrf": csrf, "jti": str(refresh.last_access_jti), "fresh": False}), 
                                          config=accessTokenConfig)
            else:
                access_token = encode(secret=private_key_pem, 
                                          token=token.AccessToken({"sub": str(user.id), "csrf": csrf, "jti": str(refresh.last_access_jti), "fresh": False}), 
                                          config=accessTokenConfig)
            
            refresh_token = encode(secret=private_key_pem,
                              token=token.RefreshToken({"jti": str(refresh.id), "csrf": csrf}),
                              config=refreshTokenConfig)

            session.commit()

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "access_exp_seconds": accessTokenConfig.exp_seconds,
                "refresh_exp_seconds": refreshTokenConfig.exp_seconds,
                "csrf": csrf
            }
        else:
            raise HTTPException(status_code=406, detail="The access jti dosen't match")

@app.get("/revoke/{refresh_token}")
def token_pair_revocation(refresh_token: str):
    with Session() as session:
        refresh_token_db = session.execute(select(RefreshToken).where(RefreshToken.id == refresh_token)).scalar_one_or_none()
        if refresh_token_db is None:
            raise HTTPException(status_code=404, detail="There is no such refresh token")
        
        last_access_jti = refresh_token_db.last_access_jti
        session.delete(refresh_token_db)
        session.commit()
        redis_client.set(str(last_access_jti), "blocked", ex=accessTokenConfig.exp_seconds)

@app.get("/check_revocation/{access_token}")
def check_access_token_for_revocation(access_token: str):
    value = redis_client.get(access_token)
    if value is None:
        raise HTTPException(status_code=404, detail="Access token not found")
    return value

# -| users |-
@app.post("/user")
def create_user(post_data: create_user_POST):
    password_bytes = post_data.password.encode("utf-8")
    password_hash = hashpw(password_bytes, gensalt())
    if not validators.email(post_data.email):
        raise HTTPException(status_code=400, detail="email is incorrect")
    with Session() as session:
        user = User(username=post_data.username, email=post_data.email, password_hash=password_hash)
        session.add(user)
        session.commit()
        return {"user_id": user.id}
