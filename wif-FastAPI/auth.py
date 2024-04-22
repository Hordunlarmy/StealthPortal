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
from bearer import OAuth2PasswordBearerWithCookie


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
    authenticated: bool = True


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="/login")


class OAuth2PasswordBearerWithCookie(OAuth2):
    def __init__(
        self,
        tokenUrl: str,
        scheme_name: Optional[str] = None,
        scopes: Optional[Dict[str, str]] = None,
        auto_error: bool = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(
            password={"tokenUrl": tokenUrl, "scopes": scopes})
        super().__init__(flows=flows, scheme_name=scheme_name, auto_error=auto_error)

    async def __call__(self, request: Request) -> Optional[str]:
        # changed to accept access token from httpOnly Cookie
        authorization: str = request.cookies.get("access_token")
        print("access_token is", authorization)

        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                return None
        return param


def verify_passwd(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def hash_passwd(password):
    return pwd_context.hash(password)


async def login_user(response, user, remember):
    persist = timedelta(minutes=30)
    if remember:
        persist = timedelta(days=30)

    access_token = create_access_token(
        user.username, user.email, user.id, persist)
    response.set_cookie(key="access_token",
                        value=f"Bearer {access_token}", httponly=True)
    print("JWToken", access_token)
    return Token(access_token=access_token, token_type="bearer")


async def logout_user(response):
    response.delete_cookie(key="access_token", path='/', httponly=True)
    print("Logout sucesseful")
    return {"message": "You have been successfully logged out."}


def create_access_token(username: str, email: str,
                        user_id: int, expires_delta: timedelta):
    from main import app
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
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expiredd")
    except JWTError:
        raise credentials_exception


async def current_user(user: Annotated[TokenData, Depends(get_current_user)]):
    user_data = user
    if user_data is None:
        user_data["authenticated"] = False
        raise HTTPException(status_code=400, detail="Inactive user")
    return user_data
