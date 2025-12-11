from typing import List, Optional

# Correctly import the unified hashing utility from core/security
from core.security import get_password_hash

# Assuming these models/schemas are defined elsewhere
from domain.user.user_models import User
from domain.user.user_schemas import UserCreate, UserUpdate
from infrastructure.user.user_repository import UserRepository


class UserService:
    """
    Business logic layer for User-related operations.
    Relies on UserRepository for database interaction.
    """

    def __init__(self, repository: UserRepository):
        """Initializes the service with the injected UserRepository."""
        self.repository = repository

    async def create_user(self, user_in: UserCreate) -> User:
        """
        Creates a new user, hashing the password before saving.
        """
        # Check if user already exists (optional, but good practice)
        existing_user = await self.repository.get_by_email(email=user_in.email)
        if existing_user:
            # In a real FastAPI app, you would raise an HTTPException
            raise ValueError("Email already registered.")

        # Hash the password using the utility from core/security
        hashed_password = get_password_hash(user_in.password)

        db_user = User(
            email=user_in.email,
            hashed_password=hashed_password,
            is_active=True,
            is_superuser=False,
            # Add other required fields from UserCreate model
            age=user_in.age,
            goal=user_in.goal,
            equipment=user_in.equipment,
        )

        return await self.repository.create(db_user)

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Fetches a user by ID."""
        return await self.repository.get_by_id(user_id=user_id)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Fetches a user by email."""
        return await self.repository.get_by_email(email=email)

    async def update_user(self, user_id: int, user_update: UserUpdate) -> Optional[
        User]:
        """
        Updates a user's details. Handles optional password hashing if provided.
        """
        update_data = user_update.model_dump(exclude_unset=True)

        if 'password' in update_data:
            # Hash new password if provided, using the core utility
            update_data['hashed_password'] = get_password_hash(
                update_data.pop('password'))

        return await self.repository.update(user_id=user_id, update_data=update_data)

    async def get_all_users(self) -> List[User]:
        """Fetches all users."""
        return await self.repository.get_all()
