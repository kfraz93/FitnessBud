from fastapi import Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from domain.auth.auth_service import decode_access_token
from domain.shared.schemas import TokenData
from domain.shared.schemas import UserOut
from domain.workout.workout_log_service import WorkoutLogService

# Local imports
from infrastructure.db import get_db_session
from infrastructure.orm_models import User as UserModel
from infrastructure.user.user_repository import UserRepository
from infrastructure.workout.workout_log_repository import WorkoutLogRepository

# OAuth2PasswordBearer handles token extraction from the header.
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl="/v1/auth/token"
)


def get_user_repository(
        session: AsyncSession = Depends(get_db_session)) -> UserRepository:   # noqa: B008
    """Dependency that provides a UserRepository instance."""
    return UserRepository(db_session=session)


async def get_current_user(
        # Get the raw JWT token string from the request header
        token: str = Security(reusable_oauth2),
        # Inject the repository dependency for database lookup
        repo: UserRepository = Depends(get_user_repository),   # noqa: B008
) -> UserOut:
    """
    Decodes the JWT token, verifies the user, and returns the UserOut object.
    Used as a dependency in all protected API endpoints.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 1. Decode the token to get the user ID
    token_data: TokenData | None = decode_access_token(token=token)

    if token_data is None:
        raise credentials_exception

    # 2. Look up the user in the database
    db_user: UserModel | None = await repo.get_by_id(user_id=token_data.user_id)

    # 3. Validation checks
    if db_user is None:
        raise credentials_exception

    if not db_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    # 4. Return the validated Pydantic model for use in the endpoint function
    return UserOut.model_validate(db_user)

def get_workout_log_repository(
        session: AsyncSession = Depends(get_db_session)) -> WorkoutLogRepository:   # noqa: B008
    """Dependency that provides a WorkoutLogRepository instance."""
    return WorkoutLogRepository(db_session=session)


def get_workout_log_service(
        repository: WorkoutLogRepository = Depends(get_workout_log_repository)) -> WorkoutLogService:   # noqa: B008
    """Dependency that provides a WorkoutLogService instance, injecting the repository."""
    # The service layer now receives the pre-configured repository instance.
    return WorkoutLogService(repository=repository)
