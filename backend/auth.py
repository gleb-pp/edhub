from datetime import UTC, datetime

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from passlib.context import CryptContext

from settings.auth import auth_settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
pwd_hasher = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """Decode JWT token and return user email."""
    payload = jwt.decode(
        token,
        auth_settings.jwt_secret_key,
        algorithms=[auth_settings.algorithm],
    )
    expire_timestamp = payload.get("exp")
    user_email = payload.get("email")

    # checking the fields
    if expire_timestamp is None or user_email is None:
        raise HTTPException(status_code=401, detail="Invalid token structure")

    # checking token expiration time
    if datetime.now(tz=UTC) > datetime.fromtimestamp(expire_timestamp, tz=UTC):
        raise HTTPException(status_code=401, detail="Token expired")

    return user_email
