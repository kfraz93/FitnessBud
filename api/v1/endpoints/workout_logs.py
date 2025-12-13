from fastapi import APIRouter
from fastapi import Depends
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from domain.shared.schemas import UserOut
from domain.shared.schemas import WorkoutLogCreate
from domain.shared.schemas import WorkoutLogOut
from domain.shared.schemas import WorkoutLogUpdate
from domain.workout.workout_log_service import WorkoutLogService
from infrastructure.db import get_db_session
from infrastructure.orm_models import WorkoutLog  # For internal type hints
from infrastructure.workout.workout_log_repository import WorkoutLogRepository

router = APIRouter(
    prefix="/workout_logs",
    tags=["Workout Logs"],
)


# Dependency injection for the WorkoutLog Service
def get_workout_log_service(
        session: AsyncSession = Depends(get_db_session)) -> WorkoutLogService:    # noqa: B008
    """Provides a WorkoutLogService instance initialized with a database session."""
    workout_repository = WorkoutLogRepository(db_session=session)
    return WorkoutLogService(repository=workout_repository)


# 1. CREATE (POST)
@router.post(
    "/",
    response_model=WorkoutLogOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new workout log"
)
async def create_log(
        log_in: WorkoutLogCreate,
        current_user: UserOut = Depends(get_current_user),  # noqa: B008
        service: WorkoutLogService = Depends(get_workout_log_service)  # noqa: B008
):
    """Saves a new workout log, linking it to the authenticated user."""

    db_log: WorkoutLog = await service.create_log(
        log_in=log_in,
        user_id=current_user.id
    )
    return WorkoutLogOut.model_validate(db_log)


# 2. READ ALL (GET)
@router.get(
    "/",
    response_model=list[WorkoutLogOut],
    summary="Retrieve all workout logs for the current user"
)
async def get_all_logs(
        current_user: UserOut = Depends(get_current_user),  # noqa: B008
        service: WorkoutLogService = Depends(get_workout_log_service)  # noqa: B008
):
    """Fetches a list of all workout logs created by the authenticated user."""

    db_logs: list[WorkoutLog] = await service.get_all_logs_by_user(
        user_id=current_user.id
    )
    # Validate each ORM model into the Pydantic output schema
    return [WorkoutLogOut.model_validate(log) for log in db_logs]


# 3. READ ONE (GET)
@router.get(
    "/{log_id}",
    response_model=WorkoutLogOut,
    summary="Retrieve a specific workout log"
)
async def get_log(
        log_id: int,
        current_user: UserOut = Depends(get_current_user),  # noqa: B008
        service: WorkoutLogService = Depends(get_workout_log_service)  # noqa: B008
):
    """Retrieves a single workout log by ID, ensuring ownership."""

    db_log: WorkoutLog = await service.get_log_by_id(
        log_id=log_id,
        user_id=current_user.id
    )
    # The service handles the 404/access denied check.
    return WorkoutLogOut.model_validate(db_log)


# 4. UPDATE (PUT/PATCH)
@router.patch(
    "/{log_id}",
    response_model=WorkoutLogOut,
    summary="Update a workout log (partial update)"
)
async def update_log(
        log_id: int,
        log_update: WorkoutLogUpdate,
        current_user: UserOut = Depends(get_current_user),  # noqa: B008
        service: WorkoutLogService = Depends(get_workout_log_service)  # noqa: B008
):
    """Updates one or more fields of an existing workout log, ensuring ownership."""

    db_log: WorkoutLog = await service.update_log(
        log_id=log_id,
        user_id=current_user.id,
        log_update=log_update
    )
    return WorkoutLogOut.model_validate(db_log)


# 5. DELETE (DELETE)
@router.delete(
    "/{log_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a specific workout log"
)
async def delete_log(
        log_id: int,
        current_user: UserOut = Depends(get_current_user),  # noqa: B008
        service: WorkoutLogService = Depends(get_workout_log_service)  # noqa: B008
):
    """Deletes a workout log by ID, ensuring ownership."""

    await service.delete_log(
        log_id=log_id,
        user_id=current_user.id
    )
