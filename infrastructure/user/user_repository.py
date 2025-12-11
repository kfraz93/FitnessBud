from sqlalchemy import select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from domain.user.user_models import User


class UserRepository:
    """Handles persistence (CRUD) operations for the User model."""

    def __init__(self, db_session: AsyncSession):
        # Renamed self.db to self.session to avoid potential naming confusion
        self.session = db_session

    async def create(self, db_user: User) -> User:
        """
        Creates a new User record in the database using a pre-constructed ORM model.
        """
        self.session.add(db_user)
        await self.session.flush()
        await self.session.refresh(db_user)

        return db_user

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Fetches a User by their primary key ID (int)."""
        # Now calls self.session.execute
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Fetches a User by their email address."""
        # Now calls self.session.execute
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalars().first()

    async def update(self, user_id: int, update_data: dict) -> Optional[User]:
        """
        Updates an existing user's fields in the database.
        """
        stmt = sa_update(User).where(User.id == user_id).values(**update_data)

        # Now calls self.session.execute
        await self.session.execute(stmt)

        return await self.get_by_id(user_id)

    async def get_all(self) -> List[User]:
        """Fetches all User records."""
        # Now calls self.session.execute
        result = await self.session.execute(select(User))
        return list(result.scalars().all())