from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

# Local imports from Infrastructure and Domain
from infrastructure.models import WorkoutLog
from domain.schemas import WorkoutLogCreate, WorkoutLogUpdate


class WorkoutLogRepository:
    """Handles persistence (CRUD) operations for the WorkoutLog model."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def create(self, log_in: WorkoutLogCreate, user_id: int) -> WorkoutLog:
        """Creates a new WorkoutLog record associated with a user."""

        # Unpack the schema data and add the required user_id foreign key
        log_data = {
            'user_id': user_id,
            'workout_date': log_in.workout_date,  # Direct access to the date object
            'duration_min': log_in.duration_min,
            'intensity': log_in.intensity,
            'workout_type': log_in.workout_type,
            'calories_burned': log_in.calories_burned
        }
        # Create the SQLAlchemy ORM model instance
        print("DEBUG: Final log_data to ORM:", log_data)

        try:
            # 2. Instantiate the SQLAlchemy ORM model instance
            db_log = WorkoutLog(**log_data)

            # 🚨 DEBUG PRINT 2: Check if ORM instantiation succeeded
            print("DEBUG: ORM instantiation succeeded.")

            # 3. Add to session and flush
            self.db.add(db_log)
            await self.db.flush()
            await self.db.refresh(db_log)

            # 🚨 DEBUG PRINT 3: Check if flush succeeded
            print("DEBUG: DB flush succeeded.")

            return db_log

        except Exception as e:
            # 🚨 CRITICAL: Print the full error and re-raise
            print("FATAL ERROR IN REPOSITORY CREATE:", e)
            import traceback
            traceback.print_exc()
            raise e  # Re-raise the exception to send the 500 error back

    async def get_by_id(self, log_id: int, user_id: int) -> Optional[WorkoutLog]:
        """
        Fetches a specific WorkoutLog by ID, ensuring it belongs to the given user.
        This provides row-level security.
        """
        stmt = select(WorkoutLog).where(
            WorkoutLog.id == log_id,
            WorkoutLog.user_id == user_id
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_all_by_user(self, user_id: int) -> List[WorkoutLog]:
        """Fetches all WorkoutLogs for a specific user."""
        stmt = select(WorkoutLog).where(
            WorkoutLog.user_id == user_id
        ).order_by(WorkoutLog.created_at.desc())  # Order by most recent first

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update(self, log_id: int, user_id: int, log_update: WorkoutLogUpdate) -> \
            Optional[WorkoutLog]:
        """Updates an existing WorkoutLog for a specific user."""

        # 1. Fetch the existing log, ensuring ownership
        db_log = await self.get_by_id(log_id, user_id)
        if not db_log:
            return None

        # 2. Update model attributes from the Pydantic schema
        update_data = log_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_log, key, value)

        # Flush the session to register the update
        await self.db.flush()
        await self.db.refresh(db_log)

        return db_log

    async def delete(self, log_id: int, user_id: int) -> bool:
        """Deletes a specific WorkoutLog, ensuring it belongs to the user."""

        # Build the delete statement, including the user_id for security
        stmt = delete(WorkoutLog).where(
            WorkoutLog.id == log_id,
            WorkoutLog.user_id == user_id
        )

        result = await self.db.execute(stmt)

        # Check if any row was actually deleted
        if result.rowcount > 0:
            return True
        return False
