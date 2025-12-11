from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, EmailStr


class UserBase(BaseModel):
    """Base fields for a user (used for input/creation)."""
    email: EmailStr


class UserCreate(UserBase):
    """Schema for registering a new user (includes password)."""
    password: str = Field(..., min_length=8, description="Minimum 8 characters")

    # Optional profile data for ML model
    age: int = Field(..., ge=18, le=120)
    goal: str = Field(..., max_length=50, description="e.g., gain_muscle, lose_weight")
    equipment: str = Field(..., max_length=100,
                           description="e.g., full_gym, bodyweight_only")


class UserUpdate(BaseModel):
    """
    Schema for updating an existing user's profile. All fields are optional
    for partial updates, but still maintain validation constraints if present.
    """
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8, description="Minimum 8 characters")
    age: Optional[int] = Field(None, ge=18, le=120)
    goal: Optional[str] = Field(None, max_length=50, description="e.g., gain_muscle, lose_weight")
    equipment: Optional[str] = Field(None, max_length=100,
                                     description="e.g., full_gym, bodyweight_only")


class UserOut(UserBase):
    """Schema for sending user data back in a response (excludes password)."""
    id: int
    is_active: bool
    age: int
    goal: str
    equipment: str
    created_at: datetime

    #  This setting allows Pydantic to read data directly from the SQLAlchemy ORM models
    model_config = ConfigDict(from_attributes=True)