from fastapi import APIRouter, HTTPException
from fastapi import Depends
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

# Local Imports for Service, Repository, and ORM Model (if needed)
from infrastructure.db import get_db_session
from infrastructure.running.running_log_repository import RunningLogRepository # RENAMED FILE FOR CONSISTENCY
from domain.running.running_log_service import RunningLogService # RENAMED FILE/CLASS FOR CONSISTENCY
from infrastructure.orm_models import RunningLog # Assuming this will be the model name, for type hints

# Shared Imports for Authentication and Schemas
from api.deps import get_current_user
from domain.shared.schemas import UserOut
from domain.shared.schemas import RunningLogCreate # Assuming these schemas are added to shared.schemas
from domain.shared.schemas import RunningLogOut
from domain.shared.schemas import RunningLogUpdate


router = APIRouter(
    prefix="/running_logs", # Consistent prefix
    tags=["Running Logs"],
)


# Dependency injection for the RunningLog Service (Fix applied)
def get_running_log_service(
        session: AsyncSession = Depends(get_db_session)) -> RunningLogService:    # noqa: B008
    """Provides a RunningLogService instance initialized correctly with a repository."""
    # Create the Repository, which needs the session (db_session=session)
    running_repository = RunningLogRepository(db_session=session)
    # Create the Service, which needs the Repository (repository=running_repository)
    return RunningLogService(repository=running_repository)


# 1. CREATE (POST)
@router.post(
    "/",
    response_model=RunningLogOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new running log"
)
async def create_log(
        log_in: RunningLogCreate,
        current_user: UserOut = Depends(get_current_user),  # noqa: B008
        service: RunningLogService = Depends(get_running_log_service)  # noqa: B008
):
    """Saves a new running log, linking it to the authenticated user."""

    db_log: RunningLog = await service.create_log(
        log_in=log_in,
        user_id=current_user.id
    )
    return RunningLogOut.model_validate(db_log)


# 2. READ ALL (GET) - Renamed for consistency
@router.get(
    "/",
    response_model=List[RunningLogOut],
    summary="Retrieve all running logs for the current user"
)
async def get_all_logs(
        current_user: UserOut = Depends(get_current_user),  # noqa: B008
        service: RunningLogService = Depends(get_running_log_service)  # noqa: B008
):
    """Fetches a list of all running logs created by the authenticated user."""

    db_logs: list[RunningLog] = await service.get_all_logs_by_user(
        user_id=current_user.id
    )
    return [RunningLogOut.model_validate(log) for log in db_logs]


# 3. READ ONE (GET) - Added for consistency
@router.get(
    "/{log_id}",
    response_model=RunningLogOut,
    summary="Retrieve a specific running log"
)
async def get_log(
        log_id: int,
        current_user: UserOut = Depends(get_current_user),  # noqa: B008
        service: RunningLogService = Depends(get_running_log_service)  # noqa: B008
):
    """Retrieves a single running log by ID, ensuring ownership."""

    db_log: RunningLog = await service.get_log_by_id(
        log_id=log_id,
        user_id=current_user.id
    )
    return RunningLogOut.model_validate(db_log)


# 4. UPDATE (PUT/PATCH) - Added for consistency
@router.patch(
    "/{log_id}",
    response_model=RunningLogOut,
    summary="Update a running log (partial update)"
)
async def update_log(
        log_id: int,
        log_update: RunningLogUpdate,
        current_user: UserOut = Depends(get_current_user),  # noqa: B008
        service: RunningLogService = Depends(get_running_log_service)  # noqa: B008
):
    """Updates one or more fields of an existing running log, ensuring ownership."""

    db_log: RunningLog = await service.update_log(
        log_id=log_id,
        user_id=current_user.id,
        log_update=log_update
    )
    return RunningLogOut.model_validate(db_log)


# 5. DELETE (DELETE) - Added for consistency
@router.delete(
    "/{log_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a specific running log"
)
async def delete_log(
        log_id: int,
        current_user: UserOut = Depends(get_current_user),  # noqa: B008
        service: RunningLogService = Depends(get_running_log_service)  # noqa: B008
):
    """Deletes a running log by ID, ensuring ownership."""

    await service.delete_log(
        log_id=log_id,
        user_id=current_user.id
    )

# 6. ML PREDICTION (GET) - Moved from old logic
@router.get("/recommend_pace", response_model=float, summary="Predict recommended running pace")
async def get_recommended_pace(
    distance_km: float,
    current_user: UserOut = Depends(get_current_user), # noqa: B008
    service: RunningLogService = Depends(get_running_log_service) # noqa: B008
):
    """
    Predicts and returns the recommended pace (min/km) for the given distance
    based on historical data and the trained ML model.
    """
    # Validation check can be moved to the service or kept here
    if distance_km <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Distance must be greater than zero."
        )

    # Assuming the service method name will be consistent
    recommended_pace = await service.predict_recommended_pace(
        user_id=current_user.id,
        distance_km=distance_km
    )

    # Return pace rounded to two decimal places
    return round(recommended_pace, 2)