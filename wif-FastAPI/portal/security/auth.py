from fastapi.security import OAuth2
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials
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


SECRET_KEY = config("secret")
ALGORITHM = config("algorithm")
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str
    email: str
    id: int
    exp: datetime
    authenticated: bool = False


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="/login")


def verify_passwd(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def hash_passwd(password):
    return pwd_context.hash(password)


async def login_user(response, user, remember):
    persist = timedelta(minutes=3)
    if remember:
        persist = timedelta(days=30)

    access_token = await create_access_token(
        user.username, user.email, user.id, persist)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,  # JavaScript can't access the cookie
        max_age=persist.total_seconds(),  # Duration the cookie is valid
        path='/',  # Global path
        secure=False,  # Only sent over HTTPS
        samesite='Lax'  # Strict or Lax, Lax is generally a safe default
    )
    response.set_cookie(key="test", value="hello_odun",
                        httponly=True, path='/')
    print("JWToken", access_token)


async def logout_user(request):
    token = request.cookies.get("access_token")
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    print("logout Token", token)
    token.update({"exp": datetime.now(timezone.utc)})
    print("Logout sucesseful")
    return {"message": "You have been successfully logged out."}


async def create_access_token(username: str, email: str,
                              user_id: int, expires_delta: timedelta):
    to_encode = {"username": username, "email": email, "id": user_id}
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user = TokenData(**payload)
        return user
    except JWTError:
        return None


async def current_user(user: Annotated[TokenData, Depends(get_current_user)]):
    user_data = user
    print(f"-----{user_data}-----")
    if user_data is None:
        return None
        # raise HTTPException(status_code=400, detail="Inactive user")
    user_data.authenticated = True
    print(user_data)
    return user_data
