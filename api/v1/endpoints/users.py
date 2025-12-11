from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

# Local imports
from infrastructure.db import get_db_session
# Import the existing dependency function from api.deps
from api.deps import get_current_user
from domain.user.user_schemas import UserOut
from domain.user.user_service import UserService
from infrastructure.user.user_repository import UserRepository

# --- Router Initialization ---
# Prefix is set to "/users"
# NOTE: This router MUST be defined and exported for main.py to import it.
user_router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

# --- Dependency Functions ---
def get_user_repository(session: AsyncSession = Depends(get_db_session)) -> UserRepository:
    """Dependency that provides a UserRepository instance."""
    return UserRepository(db_session=session)

def get_user_service(
        session: AsyncSession = Depends(get_db_session),
        repository: UserRepository = Depends(get_user_repository)
    ) -> UserService:
    """Provides a UserService instance initialized with a database session and repository."""
    return UserService(repository=repository)

# --- Endpoints ---

@user_router.get(
    "/me",
    response_model=UserOut,
    summary="Get details of the current authenticated user",
    status_code=status.HTTP_200_OK,
)
async def read_users_me(
    # Using the existing dependency from api.deps, which enforces authentication and active status
    current_user: UserOut = Depends(get_current_user)
):
    """
    Retrieves the details of the currently authenticated user.
    Requires a valid 'access_token' cookie or Authorization header token.
    """
    # The dependency returns a UserOut model, so we can return it directly.
    return current_user