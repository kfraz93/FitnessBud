from typing import Optional
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import String, Integer, Float, ForeignKey, DateTime, Date
import datetime

from infrastructure.db import Base

class WorkoutLog(Base):
    """SQLAlchemy Model for the 'workout_logs' table."""
    __tablename__ = "workout_logs"

    # CORE FIELDS (Including Primary Key and Timestamps)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=datetime.datetime.now(datetime.UTC))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=datetime.datetime.now(datetime.UTC), onupdate=datetime.datetime.now(datetime.UTC))
    workout_date: Mapped[datetime.date] = mapped_column(
        Date)  # Import 'Date' from sqlalchemy
    # Foreign Key linking back to the User model
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # Log details (Fields matching Pydantic schema)
    duration_min: Mapped[int] = mapped_column(Integer)
    intensity: Mapped[str] = mapped_column(String(50))
    workout_type: Mapped[str] = mapped_column(String(50))
    calories_burned: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationships (Link back to the User)
    user: Mapped["User"] = relationship("User", back_populates="logs")

    def __repr__(self):
        return f"<WorkoutLog(id={self.id}, user_id={self.user_id}, type='{self.workout_type}')>"