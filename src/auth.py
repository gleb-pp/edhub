from datetime import UTC, datetime

import bcrypt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from jose.exceptions import JWTError

from src.settings.auth import auth_settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def hash_password(password: str) -> str:
    """Hash the provided password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify that the provided password matches the stored password hash."""
    return bcrypt.checkpw(
        password.encode("utf-8"),
        password_hash.encode("utf-8"),
    )


def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """Decode JWT token and return user email."""
    try:
        payload = jwt.decode(
            token,
            auth_settings.jwt_secret_key,
            algorithms=[auth_settings.algorithm],
        )
        expire_timestamp = payload.get("exp")
        user_email = payload.get("sub")
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid token") from e

    # checking the fields
    if expire_timestamp is None or user_email is None:
        raise HTTPException(status_code=401, detail="Invalid token structure")

    # checking token expiration time
    if datetime.now(tz=UTC) > datetime.fromtimestamp(expire_timestamp, tz=UTC):
        raise HTTPException(status_code=401, detail="Token expired")

    return user_email
