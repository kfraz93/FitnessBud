from sqlalchemy import delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

# Shared Imports from Domain and Infrastructure
from domain.shared.schemas import RunningLogCreate  # Using consistent shared schemas
from domain.shared.schemas import RunningLogUpdate
from infrastructure.orm_models import \
    RunningLog  # Assuming the ORM model is named RunningLog


class RunningLogRepository:
    """Handles persistence (CRUD) operations for the RunningLog model."""

    def __init__(self, db_session: AsyncSession):
        # Using self.db for consistency with WorkoutLogRepository
        self.db = db_session

    # --- Standard CRUD Operations (Matching WorkoutLogRepository) ---

    async def create(self, log_in: RunningLogCreate, user_id: int) -> RunningLog:
        """Creates a new RunningLog record associated with a user."""

        # Unpack schema data and add user_id
        log_data = {
            'user_id': user_id,
            # Note: Assuming ORM fields match schema fields (e.g., running_date, pace_min_per_km)
            **log_in.model_dump()
        }

        # Calculate pace (min/km) for storage in the ORM model
        distance = log_in.distance_km
        duration = log_in.duration_min
        pace = duration / distance if distance else 0.0  # Handle division by zero

        log_data['pace_min_per_km'] = pace

        # Create the SQLAlchemy ORM model instance
        db_log = RunningLog(**log_data)

        # Add to session and flush
        self.db.add(db_log)
        await self.db.flush()
        await self.db.refresh(db_log)

        # NOTE: COMMIT is handled by the RunningLogService layer

        return db_log

    async def get_by_id(self, log_id: int, user_id: int) -> RunningLog | None:
        """
        Fetches a specific RunningLog by ID, ensuring it belongs to the given user.
        """
        stmt = select(RunningLog).where(
            RunningLog.id == log_id,
            RunningLog.user_id == user_id
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_all_by_user(self, user_id: int) -> list[RunningLog]:
        """Fetches all RunningLogs for a specific user (Descending order for API display)."""
        stmt = select(RunningLog).where(
            RunningLog.user_id == user_id
        ).order_by(RunningLog.created_at.desc())

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update(self, log_id: int, user_id: int, log_update: RunningLogUpdate) -> \
            RunningLog | None:
        """Updates an existing RunningLog for a specific user."""

        # 1. Fetch the existing log, ensuring ownership
        db_log = await self.get_by_id(log_id, user_id)
        if not db_log:
            return None

        # 2. Update model attributes from the Pydantic schema
        update_data = log_update.model_dump(exclude_unset=True)

        # If distance or duration is updated, recalculate pace
        if 'distance_km' in update_data or 'duration_min' in update_data:
            new_distance = update_data.get('distance_km', db_log.distance_km)
            new_duration = update_data.get('duration_min', db_log.duration_min)
            update_data[
                'pace_min_per_km'] = new_duration / new_distance if new_distance else 0.0

        for key, value in update_data.items():
            setattr(db_log, key, value)

        # Flush the session to register the update
        await self.db.flush()
        await self.db.refresh(db_log)

        return db_log

    async def delete(self, log_id: int, user_id: int) -> bool:
        """Deletes a specific RunningLog, ensuring it belongs to the user."""

        stmt = delete(RunningLog).where(
            RunningLog.id == log_id,
            RunningLog.user_id == user_id
        )

        result = await self.db.execute(stmt)
        return result.rowcount > 0

    # --- ML Feature Fetcher (Specific to Running) ---

    async def get_all_by_user_raw(self, user_id: int) -> List[RunningLog]:
        """
        Fetches ALL run logs for a user, ordered OLDEST to NEWEST (ASCENDING).
        CRITICAL for the Pandas rolling average calculation in the Service layer.
        """
        stmt = (
            select(RunningLog)
            .where(RunningLog.user_id == user_id)
            .order_by(RunningLog.running_date.asc())  # Order by the run date
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
