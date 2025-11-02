from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from infrastructure.db import get_db_session
from domain.schemas import WorkoutLogCreate, WorkoutLogOut, WorkoutLogUpdate, UserOut
from domain.workout_log_service import WorkoutLogService
from infrastructure.models import WorkoutLog  # For internal type hints
from api.deps import get_current_user

router = APIRouter(
    prefix="/workout_logs",
    tags=["Workout Logs"],
)

# Dependency injection for the WorkoutLog Service
def get_workout_log_service(session: AsyncSession = Depends(get_db_session)) -> WorkoutLogService:
    """Provides a WorkoutLogService instance initialized with a database session."""
    return WorkoutLogService(session=session)

# 1. CREATE (POST)
@router.post(
    "/",
    response_model=WorkoutLogOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new workout log"
)
async def create_log(
        log_in: WorkoutLogCreate,
        current_user: UserOut = Depends(get_current_user),
        service: WorkoutLogService = Depends(get_workout_log_service)
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
    response_model=List[WorkoutLogOut],
    summary="Retrieve all workout logs for the current user"
)
async def get_all_logs(
        current_user: UserOut = Depends(get_current_user),
        service: WorkoutLogService = Depends(get_workout_log_service)
):
    """Fetches a list of all workout logs created by the authenticated user."""

    db_logs: List[WorkoutLog] = await service.get_all_logs_by_user(
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
        current_user: UserOut = Depends(get_current_user),
        service: WorkoutLogService = Depends(get_workout_log_service)
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
        current_user: UserOut = Depends(get_current_user),
        service: WorkoutLogService = Depends(get_workout_log_service)
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
        current_user: UserOut = Depends(get_current_user),
        service: WorkoutLogService = Depends(get_workout_log_service)
):
    """Deletes a workout log by ID, ensuring ownership."""

    await service.delete_log(
        log_id=log_id,
        user_id=current_user.id
    )
