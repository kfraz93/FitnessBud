import datetime
from datetime import timedelta
from typing import Annotated, Optional

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

# Local imports
from core.config import settings
from domain.user.user_models import User
from infrastructure.db import get_db_session
from infrastructure.user.user_repository import UserRepository

# --- Password Hashing and Verification ---

ph = PasswordHasher()


def get_password_hash(password: str) -> str:
    """Hashes a plaintext password using Argon2."""
    return ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a hash."""
    try:
        # FIX: Swapped the arguments to (password, hash).
        # The PasswordHasher.verify() method expects the plaintext password first,
        # followed by the stored hash string.
        ph.verify(plain_password, hashed_password)
        return True
    except VerifyMismatchError:
        return False


# --- JWT Token Generation ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.now(datetime.timezone.utc) + expires_delta
    else:
        expire = datetime.datetime.now(datetime.timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # We use 'sub' (subject) to store the user identifier
    to_encode.update({"exp": expire, "sub": data.get("user_id")})

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY,
                             algorithm=settings.ALGORITHM)
    return encoded_jwt


# --- Authentication Dependencies ---

# This scheme is only used for OpenAPI documentation/Swagger UI and form data login
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="v1/auth/token")


async def get_token_from_request(request: Request) -> Optional[str]:
    """
    Custom dependency to extract the token from either the HTTP-only cookie 
    or the standard Authorization header.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 1. Check Cookie first (preferred for web clients)
    cookie_token = request.cookies.get("access_token")
    if cookie_token and cookie_token.startswith("Bearer "):
        return cookie_token.split(" ")[1]  # Extract the token part

    # 2. Check Authorization header (for standard API clients)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]  # Extract the token part

    # If neither is found, let the main dependency raise the exception
    return None


async def get_current_user(
        token: Annotated[Optional[str], Depends(get_token_from_request)],
        db_session: AsyncSession = Depends(get_db_session)
) -> User:
    """
    Decodes and validates the JWT token, then fetches the corresponding user from the database.
    This dependency can be used in all protected endpoints.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if token is None:
        raise credentials_exception

    try:
        # Decode the JWT token
        payload = jwt.decode(token, settings.SECRET_KEY,
                             algorithms=[settings.ALGORITHM])

        # 'sub' is the subject, which holds our user_id
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # Fetch the user from the database
    user_repository = UserRepository(db_session=db_session)
    # Convert user_id back to int for database query
    user = await user_repository.get_by_id(user_id=int(user_id))

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
        current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    Ensures the retrieved user is active. Used for most protected operations.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user