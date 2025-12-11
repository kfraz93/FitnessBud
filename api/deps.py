from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
# Removed unnecessary imports: HTTPException, status, Request, Optional, UUID, TokenData

# Import the core active user dependency from core.security. This replaces the need
# for the custom token extraction and user ID decoding logic previously attempted.
from core.security import get_current_active_user

# Local imports
from infrastructure.db import get_db_session

from infrastructure.workout.workout_log_repository import WorkoutLogRepository
from domain.workout.workout_log_service import WorkoutLogService
from infrastructure.user.user_repository import UserRepository
from domain.user.user_schemas import UserOut
# We need to import the ORM model type to match the return type of get_current_active_user
from domain.user.user_models import User as UserModel


def get_user_repository(
        session: AsyncSession = Depends(get_db_session)) -> UserRepository:
    """Dependency that provides a UserRepository instance."""
    return UserRepository(db_session=session)


def get_current_user_out(
        # Use the core dependency that handles token validation, activity check, and returns the ORM model
        db_user: UserModel = Depends(get_current_active_user)
) -> UserOut:
    """
    Dependency to be used in API endpoints. It ensures the user is authenticated and active,
    and converts the database model (UserModel) into the public schema (UserOut).
    """
    # The get_current_active_user dependency already raises 401/400 exceptions if the user is invalid or inactive.
    return UserOut.model_validate(db_user)

# Alias the function to 'get_current_user' for backwards compatibility with API route dependencies.
get_current_user = get_current_user_out


def get_workout_log_repository(
        session: AsyncSession = Depends(get_db_session)) -> WorkoutLogRepository:
    """Dependency that provides a WorkoutLogRepository instance."""
    return WorkoutLogRepository(db_session=session)


def get_workout_log_service(
        repository: WorkoutLogRepository = Depends(
            get_workout_log_repository)) -> WorkoutLogService:
    """Dependency that provides a WorkoutLogService instance, injecting the repository."""
    return WorkoutLogService(repository=repository)