from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

# Local Imports for Service and Repository
from infrastructure.db import get_db_session
from domain.running import running_schemas
from domain.running.running_service import RunningService
from infrastructure.running.running_repository import RunningRepository

#  Local imports for authenticcation
from api.deps import get_current_user
from domain.user.user_schemas import UserOut

router = APIRouter(prefix="/running", tags=["Running Logs"])


# Dependency Injector for RunningService
def get_running_service(
        db_session: AsyncSession = Depends(get_db_session)) -> RunningService:
    """Provides a RunningService instance with a repository bound to the current session."""
    repository = RunningRepository(session=db_session)
    return RunningService(repository=repository)


@router.post("/", response_model=running_schemas.RunLogResponse,
             status_code=status.HTTP_201_CREATED)
async def create_run_log(
        log_data: running_schemas.RunLogCreate,
        current_user: UserOut = Depends(get_current_user),
        service: RunningService = Depends(get_running_service)
):
    """Logs a new run entry for the authenticated user."""
    # The service layer handles pace calculation
    return await service.log_run(current_user.id, log_data)


@router.get("/", response_model=List[running_schemas.RunLogResponse])
async def get_user_run_history(
        current_user: UserOut = Depends(get_current_user),
        service: RunningService = Depends(get_running_service)
):
    """Retrieves all run logs for the authenticated user."""
    return await service.get_user_run_history(current_user.id)


@router.get("/recommend_pace", response_model=float)
async def get_recommended_pace(
        distance_km: float,
        current_user: UserOut = Depends(get_current_user),
        service: RunningService = Depends(get_running_service)
):
    """
    Predicts and returns the recommended pace (min/km) for the given distance
    based on historical data and the trained ML model.
    """
    if distance_km <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Distance must be greater than zero."
        )

    recommended_pace = await service.predict_recommended_pace(current_user.id, distance_km)

    # Return pace rounded to two decimal places
    return round(recommended_pace, 2)
