from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class RunLogBase(BaseModel):
    distance_km: float = Field(..., gt=0, description="Distance in kilometers.")
    duration_min: float = Field(..., gt=0, description="Duration in minutes.")
    avg_heart_rate: Optional[int] = Field(None, gt=0, description="Average heart rate during the run.")
    run_type: str = Field("Easy", description="e.g., Easy, Tempo, Interval.")

class RunLogCreate(RunLogBase):
    pass

class RunLogResponse(RunLogBase):
    id: int
    user_id: int
    pace_min_per_km: float
    log_date: datetime

    model_config = ConfigDict(from_attributes=True)