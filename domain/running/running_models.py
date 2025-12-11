from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import datetime
from infrastructure.db import Base


class RunLog(Base):
    """SQLAlchemy ORM Model for the 'run_logs' table."""
    __tablename__ = "run_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)

    # Input Metrics
    distance_km = Column(Float, nullable=False)
    duration_min = Column(Float, nullable=False)

    # Optional/Contextual Features
    avg_heart_rate = Column(Integer, nullable=True)
    run_type = Column(String, nullable=True, default="Easy")

    # Target/Calculated Metric
    pace_min_per_km = Column(Float, nullable=False)

    log_date = Column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
        nullable=False
    )

    # Relationship to User model
    user = relationship("User", back_populates="run_logs")

    def __init__(self, **kwargs):
        # Calculation for data integrity (Pace = Duration / Distance)
        distance = kwargs.get('distance_km')
        duration = kwargs.get('duration_min')
        if distance and duration and distance > 0:
            kwargs['pace_min_per_km'] = duration / distance
        super().__init__(**kwargs)