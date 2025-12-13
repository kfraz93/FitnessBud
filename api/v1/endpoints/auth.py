from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from domain.auth import (
    auth_service,  # Used for password verification and token generation
)
from domain.shared.schemas import Token
from domain.user.user_service import UserService

# Local imports
from infrastructure.db import get_db_session

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# Reuse the UserService dependency helper
def get_user_service(session: AsyncSession = Depends(get_db_session)) -> UserService:   # noqa: B008
    return UserService(session=session)


@router.post(
    "/token",
    response_model=Token,
    summary="Authenticate user and issue JWT token",
    description="Accepts username (email) and password via OAuth2 form data."
)
async def login_for_access_token(
        # FastAPI's built-in form to handle 'username' (which is our email) and 'password'
        form_data: OAuth2PasswordRequestForm = Depends(),    # noqa: B008
        user_service: UserService = Depends(get_user_service)  # noqa: B008
):
    """
    Verifies user credentials. If valid, generates and returns an access token.
    """
    # 1. Fetch user by email (username from form_data is the email)
    user = await user_service.get_user_by_email(form_data.username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Verify password hash
    if not auth_service.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Generate token upon successful verification
    # We use user.id (int) as the unique identifier for the token payload
    token_response = auth_service.get_auth_tokens(user_id=user.id)

    return token_response
