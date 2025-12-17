from datetime import date
from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import EmailStr
from pydantic import Field

# Pydantic Schemas (Data Transfer Objects - DTOs)
# These represent the data structures used by our core business logic and API endpoints.

# --- User Schemas ---

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


# --- Workout Log Schemas ---

class WorkoutLogBase(BaseModel):
    """Base fields for a workout log."""
    workout_date: date = Field(...,
                               description="The date the workout was performed (YYYY-MM-DD).")
    duration_min: int = Field(..., gt=0)
    intensity: str = Field(..., max_length=50, description="e.g., high, moderate, low")
    workout_type: str = Field(..., max_length=50,
                              description="e.g., Strength, Cardio, Yoga",
                              )
    calories_burned: float | None = Field(None, gt=0)


class WorkoutLogCreate(WorkoutLogBase):
    """Schema for creating a new log (used in API request bodies)."""
    pass


class WorkoutLogUpdate(BaseModel):
    """Schema for updating a workout log (all fields are optional for partial updates)."""
    intensity: str | None = Field(None, description="e.g., Low, Medium, High")
    duration_min: int | None = Field(None, gt=0)
    workout_type: str | None = Field(None,
                                        description="e.g., Cardio, Strength, Yoga")
    equipment_used: str | None = Field(None,
                                          description="e.g., Dumbbells, Mat, None")
    calories_burned: float | None = Field(None, gt=0)


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


# --- Running Log Schemas (New) ---

class RunningLogBase(BaseModel):
    """Base fields for a running log."""
    # Renamed log_date to running_date for consistency with workout_date
    running_date: date = Field(...,
                                description="The date the run was performed (YYYY-MM-DD).")
    distance_km: float = Field(..., gt=0, description="Distance in kilometers.")
    duration_min: float = Field(..., gt=0, description="Duration in minutes.")
    avg_heart_rate: int | None = Field(None, gt=0, description="Average heart rate during the run.")
    run_type: str = Field("Easy", description="e.g., Easy, Tempo, Interval.")


class RunningLogCreate(RunningLogBase):
    """Schema for creating a new running log (used in API request bodies)."""
    pass


class RunningLogUpdate(BaseModel):
    """Schema for updating a running log (all fields are optional for partial updates)."""
    running_date: date | None = Field(None, description="The date the run was performed (YYYY-MM-DD).")
    distance_km: float | None = Field(None, gt=0, description="Distance in kilometers.")
    duration_min: float | None = Field(None, gt=0, description="Duration in minutes.")
    avg_heart_rate: int | None = Field(None, gt=0, description="Average heart rate during the run.")
    run_type: str | None = Field(None, description="e.g., Easy, Tempo, Interval.")


class RunningLogOut(RunningLogBase):
    """Schema for returning a running log record, including generated IDs, timestamps, and calculated pace."""
    id: int
    user_id: int
    pace_min_per_km: float # This field is calculated, but included in the response
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class RunningLog(RunningLogBase):
    """Schema for reading a running log (including metadata)."""
    id: int
    user_id: int
    pace_min_per_km: float
    created_at: datetime
    updated_at: datetime
    model_config = {'from_attributes': True}


# --- Auth Schemas ---

class Token(BaseModel):
    """Schema for the JWT response body sent to the client."""
    access_token: str
    token_type: str = "bearer"  # noqa: S105


class TokenData(BaseModel):
    """Schema for the payload data inside the JWT."""
    # This ID links the token back to the User in the database
    user_id: int
