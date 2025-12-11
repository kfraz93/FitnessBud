from typing import Optional
from infrastructure.user.user_repository import UserRepository
from domain.user.user_models import User
from domain.user.user_schemas import UserCreate

# Import security utilities from the core module
from core.security import verify_password, get_password_hash, create_access_token

class AuthService:
    """
    Service layer for user authentication.
    Handles high-level logic for registration and login, delegating
    data access to UserRepository and security operations to core.security.
    """

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def register_user(self, user_data: UserCreate) -> User:
        """
        Registers a new user, handling password hashing and duplicate checks.
        """
        # 1. Check for existing user
        if await self.user_repository.get_by_email(email=user_data.email):
            raise ValueError("Email already registered.")

        # 2. Hash the password using core utility
        hashed_password = get_password_hash(user_data.password)

        # 3. Create the user model instance
        # Note: We rely on the Pydantic model validation, but for the ORM,
        # we construct it explicitly to ensure the hashed password is used.
        new_user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            age=user_data.age,
            goal=user_data.goal,
            equipment=user_data.equipment,
            is_active=True
        )

        # 4. Save to database via repository
        created_user = await self.user_repository.create(new_user)
        return created_user

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Verifies credentials for login.
        Returns the User object if successful, None otherwise.
        """
        # 1. Fetch User from DB
        user = await self.user_repository.get_by_email(email=email)

        if not user:
            return None

        # 2. Verify Password using core utility
        if not verify_password(password, user.hashed_password):
            return None

        return user