from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from domain.auth_service import verify_password

from domain.schemas import UserCreate
from domain import auth_service

from infrastructure.user_repository import UserRepository
from infrastructure.models import User


class UserService:
    """
    Handles core user business logic, combining data access (Repository)
    and authentication rules (Auth Service).
    """

    def __init__(self, session: AsyncSession):
        # The service layer holds the repository instance
        self.repository = UserRepository(db_session=session)

    async def create_new_user(self, user_in: UserCreate) -> User:
        """
        Creates a new user, hashes the password, and checks for email conflicts.
        """
        # 1. Check for existing user (Domain Rule)
        existing_user = await self.repository.get_by_email(user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Account with this email already exists."
            )

        # 2. Hash the password (Domain Rule via Auth Service)
        hashed_password = auth_service.hash_password(user_in.password)

        # 3. Save to database (Infrastructure/Repository)
        db_user = await self.repository.create(
            user_in=user_in,
            hashed_password=hashed_password
        )

        await self.repository.db.commit()

        return db_user

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Retrieves a user by email."""
        return await self.repository.get_by_email(email)

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Retrieves a user by ID."""
        return await self.repository.get_by_id(user_id)

    async def get_all_users(self) -> List[User]:
        """Retrieves all users (for administrative/testing purposes)."""
        return await self.repository.get_all()

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticates a user by email and password."""
        db_user = await self.repository.get_by_email(email=email)

        # 1. Check if user exists
        if not db_user:
            return None

        # 2. Check if password is valid using the Auth Service
        if not verify_password(plain_password=password,
                               hashed_password=db_user.hashed_password):
            return None

        # 3. If credentials are valid, return the user model
        return db_user
