from fastapi.security import (OAuth2, OAuth2PasswordBearer,
                              OAuth2PasswordRequestForm, HTTPBearer,
                              HTTPAuthorizationCredentials)
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security.utils import get_authorization_scheme_param
from fastapi import HTTPException, status, Request, Depends, Response
from typing import Optional, Dict, Annotated
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from decouple import config
from .bearer import OAuth2PasswordBearerWithCookie


SECRET_KEY = config(
    "secret", default="cee619cd280708255b2ea19f56d24931d055d4148a8ed18688c962")
ALGORITHM = config("algorithm", default="HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 30
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="/login")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str
    email: str
    id: int
    exp: datetime
    authenticated: bool = False


def verify_passwd(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def hash_passwd(password):
    return pwd_context.hash(password)


async def login_user(response, user, remember):
    persist = timedelta(minutes=3)
    cookie_config = config('server', default="development")
    if remember:
        persist = timedelta(days=30)

    access_token = await create_access_token(
        user.username, user.email, user.id, persist)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        # JavaScript can't access the cookie
        httponly=False if cookie_config == 'development' else True,
        max_age=persist.total_seconds(),  # Duration the cookie is valid
        path='/',  # Global path
        # Only sent over HTTPS
        secure=False if cookie_config == 'development' else True,
        samesite='Lax'  # Strict or Lax, Lax is generally a safe default
    )
    return response


async def logout_user(response):
    response.delete_cookie("access_token")


async def create_access_token(username: str, email: str,
                              user_id: int, expires_delta: timedelta):
    to_encode = {"username": username, "email": email, "id": user_id}
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    if token is None:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user = TokenData(**payload)
        return user
    except JWTError:
        return None


async def current_user(user: Annotated[TokenData, Depends(get_current_user)]):
    user_data = user
    if user_data is None:
        return None
        # raise HTTPException(status_code=400, detail="Inactive user")
    user_data.authenticated = True
    return user_data
