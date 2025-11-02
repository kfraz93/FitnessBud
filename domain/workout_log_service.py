from typing import List
from fastapi import HTTPException, status

# Domain Layer Imports
from domain.schemas import WorkoutLogCreate, WorkoutLogUpdate, \
    WorkoutLog as WorkoutLogOut
from infrastructure.models import WorkoutLog
from infrastructure.workout_log_repository import WorkoutLogRepository


class WorkoutLogService:
    """
    Handles all business logic and coordination for workout logs.
    Ensures data consistency and user ownership.
    """

    def __init__(self, repository: WorkoutLogRepository):
        # Store the repository instance passed to the constructor
        self.repository = repository

    async def create_log(self, log_in: WorkoutLogCreate, user_id: int) -> WorkoutLog:
        """Creates a new workout log and commits the transaction."""

        # Persistence call
        db_log = await self.repository.create(log_in=log_in, user_id=user_id)

        # Commit the transaction after successful creation
        await self.repository.db.commit()

        return db_log

    async def get_log_by_id(self, log_id: int, user_id: int) -> WorkoutLog:
        """Fetches a single log, ensuring it belongs to the user."""
        db_log = await self.repository.get_by_id(log_id=log_id, user_id=user_id)

        if not db_log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workout log not found or access denied."
            )
        return db_log

    async def get_all_logs_by_user(self, user_id: int) -> List[WorkoutLog]:
        """Fetches all logs for a user."""
        return await self.repository.get_all_by_user(user_id=user_id)

    async def update_log(self, log_id: int, user_id: int,
                         log_update: WorkoutLogUpdate) -> WorkoutLog:
        """Updates an existing log for a specific user and commits."""

        # Persistence call
        db_log = await self.repository.update(
            log_id=log_id,
            user_id=user_id,
            log_update=log_update
        )

        if not db_log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workout log not found or access denied."
            )

        # Commit the transaction
        await self.repository.db.commit()

        return db_log

    async def delete_log(self, log_id: int, user_id: int) -> None:
        """Deletes a log for a specific user and commits."""

        # Persistence call
        deleted = await self.repository.delete(log_id=log_id, user_id=user_id)

        if not deleted:
            # Note: We check for not deleted and raise 404, providing a clean response
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workout log not found or access denied."
            )

        # Commit the transaction after successful deletion
        await self.repository.db.commit()
