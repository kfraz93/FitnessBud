from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from infrastructure.models import User
from domain.schemas import UserCreate


class UserRepository:
    """Handles persistence (CRUD) operations for the User model."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def create(self, user_in: UserCreate, hashed_password: str) -> User:
        """Creates a new User record in the database."""

        # Unpack the schema data into a dictionary
        user_data = user_in.model_dump()

        # Replace the plaintext password from the schema with the hashed version
        user_data['hashed_password'] = hashed_password
        # Remove the original plaintext password key to avoid saving it
        del user_data['password']

        # Create the SQLAlchemy ORM model instance
        db_user = User(**user_data)

        # Add the instance to the session
        self.db.add(db_user)
        # Flush the session to assign an ID (primary key) to the object
        await self.db.flush()
        # Refresh the object to get the ID and other defaults
        await self.db.refresh(db_user)

        return db_user

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Fetches a User by their primary key ID."""
        # This executes a SELECT query: SELECT * FROM users WHERE id = :user_id
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Fetches a User by their email address."""
        # Executes a SELECT query: SELECT * FROM users WHERE email = :email
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalars().first()

    async def get_all(self) -> List[User]:
        """Fetches all User records."""
        result = await self.db.execute(select(User))
        return list(result.scalars().all())

    # NOTE: Update/Delete methods will be added later as needed.
