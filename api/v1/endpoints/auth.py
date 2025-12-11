from typing import Annotated
from datetime import timedelta

from fastapi import APIRouter, Depends, status, Body, Response, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

# Local imports
from core.config import settings
from core.security import create_access_token
from infrastructure.db import get_db_session
from infrastructure.user.user_repository import UserRepository
from domain.user.user_schemas import UserCreate, UserOut
from domain.auth.auth_service import AuthService
from domain.auth.auth_schemas import Token

# --- Router Initialization ---
auth_router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# --- Dependency Injection ---

def get_auth_service(db_session: AsyncSession = Depends(get_db_session)) -> AuthService:
    """
    Provides the AuthService instance by injecting its dependency, UserRepository,
    wired up to the current DB session.
    """
    user_repository = UserRepository(db_session=db_session)
    return AuthService(user_repository=user_repository)


# --- Endpoints ---

@auth_router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account and set auth cookie"
)
async def register_user(
        user_in: UserCreate = Body(..., description="Details for user registration."),
        auth_service: AuthService = Depends(get_auth_service),
        response: Response = Response()
):
    """
    Handles user registration (creating a new user) and immediately logs them in
    by setting a secure authentication cookie.
    """
    # 1. Delegate registration logic to AuthService
    db_user = await auth_service.register_user(user_in)

    # 2. Create Access Token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    access_token = create_access_token(
        data={"user_id": str(db_user.id)},
        expires_delta=access_token_expires
    )

    # 3. Set the secure, HTTP-only cookie
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=int(access_token_expires.total_seconds()),
        samesite="lax",
        secure=settings.ENVIRONMENT == "production",  # True in prod, False in dev
    )

    return UserOut.model_validate(db_user)


@auth_router.post(
    "/token",
    summary="Authenticate user (Login) and return access token via HTTP-only cookie",
    status_code=status.HTTP_200_OK,
    response_model=Token
)
async def login_for_access_token(
        response: Response,
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        auth_service: AuthService = Depends(get_auth_service),
):
    """
    Authenticates a user using email (username) and password. If successful,
    it sets a secure, HTTP-only cookie containing the access token.
    """
    # 1. Authenticate User
    # Note: OAuth2 form uses 'username', but our domain uses 'email'
    user = await auth_service.authenticate_user(
        email=form_data.username,
        password=form_data.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Create Access Token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    access_token = create_access_token(
        data={"user_id": str(user.id)},
        expires_delta=access_token_expires
    )

    # 3. Set the secure, HTTP-only cookie
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=int(access_token_expires.total_seconds()),
        samesite="lax",
        secure=settings.ENVIRONMENT == "production",
    )

    # 4. Return token for API clients
    return Token(access_token=access_token, token_type="bearer")


@auth_router.post(
    "/logout",
    summary="Remove authentication cookie (Logout)",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def logout(response: Response):
    """
    Removes the secure, HTTP-only authentication cookie to log the user out.
    """
    response.delete_cookie(key="access_token")
    return response