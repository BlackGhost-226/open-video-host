from pydantic import BaseModel
from typing import Optional

class login_POST(BaseModel):
    email: str
    password: str
    user_agent: str

class refresh_POST(BaseModel):
    refresh_token: str
    last_access_jti: str
    password: Optional[str] = None

class create_user_POST(BaseModel):
    username: str
    email: str
    password: str
