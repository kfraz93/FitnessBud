from fastapi import APIRouter, Depends, status, Body
from sqlalchemy.ext.asyncio import AsyncSession

# Local imports
from infrastructure.db import get_db_session
from domain.schemas import UserCreate, UserOut
from domain.user_service import UserService
from infrastructure.models import User  # For return type hint

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


# Dependency injection for the User Service
def get_user_service(session: AsyncSession = Depends(get_db_session)) -> UserService:
    """Provides a UserService instance initialized with a database session."""
    return UserService(session=session)


@router.post(
    "/",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account"
)
async def register_user(
        # Use Body(...) to ensure the schema is applied to the request body
        user_in: UserCreate = Body(...,
                                   description="Details for user registration and ML profile."),
        user_service: UserService = Depends(get_user_service)
):
    """
    Handles user registration.
    Checks for email conflicts, hashes the password, and saves the user and their
    ML profile data (age, goal, equipment).
    """
    db_user: User = await user_service.create_new_user(user_in=user_in)

    # Use UserOut.model_validate() to convert the SQLAlchemy ORM model (db_user)
    # into the Pydantic schema for the response.
    return UserOut.model_validate(db_user)

# NOTE: Endpoints for GET /users/{id} and GET /users will be added later.
