from typing import Optional
from datetime import datetime, date
from pydantic import BaseModel, ConfigDict, Field, EmailStr


# Pydantic Schemas (Data Transfer Objects - DTOs)
# These represent the data structures used by our core business logic and API endpoints.

# User Schemas

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


#  Workout Log Schemas

class WorkoutLogBase(BaseModel):
    """Base fields for a workout log."""
    # Data validation ensures duration is positive
    workout_date: date = Field(...,
                               description="The date the workout was performed (YYYY-MM-DD).")
    duration_min: int = Field(..., gt=0)
    intensity: str = Field(..., max_length=50, description="e.g., high, moderate, low")
    workout_type: str = Field(..., max_length=50,
                              description="e.g., Strength, Cardio, Yoga",
                              )
    calories_burned: Optional[float] = Field(None, gt=0)


class WorkoutLogCreate(WorkoutLogBase):
    """Schema for creating a new log (used in API request bodies)."""
    # No extra fields needed, inherits all necessary fields from Base
    pass


class WorkoutLogUpdate(BaseModel):
    """Schema for updating a workout log (all fields are optional for partial updates)."""
    intensity: Optional[str] = Field(None, description="e.g., Low, Medium, High")
    duration_min: Optional[int] = Field(None, gt=0)
    workout_type: Optional[str] = Field(None,
                                        description="e.g., Cardio, Strength, Yoga")
    equipment_used: Optional[str] = Field(None,
                                          description="e.g., Dumbbells, Mat, None")


class WorkoutLogOut(WorkoutLogBase):
    """Schema for returning a workout log record, including generated IDs and timestamps."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class WorkoutLog(WorkoutLogBase):
    """Schema for reading a workout log."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {'from_attributes': True}


class Token(BaseModel):
    """Schema for the JWT response body sent to the client."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for the payload data inside the JWT."""
    # This ID links the token back to the User in the database
    user_id: int
