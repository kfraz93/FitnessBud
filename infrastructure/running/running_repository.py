from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from domain.running import running_models as running_models
from domain.running import running_schemas
from domain.running.running_models import RunLog


class RunningRepository:
    """
    Infrastructure Adapter: Handles asynchronous CRUD operations for RunLog entity.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_run_log(self, user_id: int,
                             log_data: running_schemas.RunLogCreate) -> running_models.RunLog:
        """Creates a new run log entry."""
        db_log = running_models.RunLog(user_id=user_id, **log_data.model_dump())

        self.session.add(db_log)
        await self.session.commit()
        await self.session.refresh(db_log)
        return db_log

    async def get_run_logs_by_user(self, user_id: int) -> List[running_models.RunLog]:
        """Retrieves all run logs for a specific user."""
        stmt = select(running_models.RunLog).filter(
            running_models.RunLog.user_id == user_id).order_by(
            running_models.RunLog.log_date.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()


    async def get_user_run_history_raw(self, user_id: int) -> List[RunLog]:
        """
        Fetches ALL run logs for a user, ordered OLDEST to NEWEST (ASCENDING).
        This specific order is CRITICAL for the Pandas rolling average calculation
        in the RunningService to correctly compute fitness over time.
        """
        stmt = (
            select(RunLog)
            .where(RunLog.user_id == user_id)
            .order_by(RunLog.log_date.asc()) # ASCENDING ORDER (oldest first)
        )
        result = await self.session.execute(stmt)
        # Returns a list of RunLog ORM objects
        return result.scalars().all()
