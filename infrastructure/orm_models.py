from typing import List, Optional
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import String, Integer, Float, ForeignKey, Boolean, DateTime, Date
import datetime

from infrastructure.db import Base


# SQLAlchemy ORM Models (Persistence Adapter)

class User(Base):
    """SQLAlchemy Model for the 'users' table."""
    __tablename__ = "users"

    # CORE FIELDS (Including Primary Key and Timestamps)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=datetime.datetime.now(datetime.UTC))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=datetime.datetime.now(datetime.UTC), onupdate=datetime.datetime.now(datetime.UTC))

    # Authentication and Core Fields
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # ML Feature Fields (User Profile) - Now correctly non-nullable
    age: Mapped[int] = mapped_column(Integer)
    goal: Mapped[str] = mapped_column(String(50))
    equipment: Mapped[str] = mapped_column(String(100))

    # Relationships (Link to Workout Logs)
    logs: Mapped[List["WorkoutLog"]] = relationship(
        "WorkoutLog",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"


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