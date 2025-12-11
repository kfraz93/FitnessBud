from typing import List, Dict, Any
from datetime import datetime, timedelta

import pandas as pd

# Application Components
from domain.running.running_schemas import RunLogCreate, RunLogResponse
from infrastructure.running.running_repository import RunningRepository


class RunningService:
    """
    Application Service (Use Case): Manages all business logic related to running logs and fitness calculation.
    It orchestrates data from the Repository and applies transformations and scoring.
    """

    def __init__(self, repository: RunningRepository):
        self.repository = repository

    @staticmethod
    def calculate_pace(distance_km: float, duration_min: float) -> float:
        """
        Calculates pace in minutes per kilometer.
        Pace = Duration (min) / Distance (km)
        """
        if distance_km == 0:
            return 0.0
        return round(duration_min / distance_km, 2)

    async def create_run_log(self, user_id: int,
                             log_data: RunLogCreate) -> RunLogResponse:
        """
        Calculates pace and persists the new run log via the repository.
        """
        pace = self.calculate_pace(log_data.distance_km, log_data.duration_min)

        # Create a dictionary suitable for the repository layer
        data_for_repo = {
            "distance_km": log_data.distance_km,
            "duration_min": log_data.duration_min,
            "avg_heart_rate": log_data.avg_heart_rate,
            "run_type": log_data.run_type,
            "pace_min_per_km": pace  # Add the calculated pace
        }

        # We convert back to RunLogCreate temporarily to ensure Pydantic validation
        run_log_to_create = RunLogCreate(**data_for_repo)

        # The repository handles the actual database object creation and commit
        db_log = await self.repository.create_run_log(user_id, run_log_to_create)

        # Convert the ORM model back to the Pydantic response schema
        return RunLogResponse.model_validate(db_log)

    async def get_user_run_history(self, user_id: int) -> List[RunLogResponse]:
        """
        Retrieves all run logs for a user and returns them as Pydantic models.

        NOTE: This method was previously named get_run_logs and was renamed for
        consistency with the controller layer.
        """
        db_logs = await self.repository.get_run_logs_by_user(user_id)
        # Use a list comprehension for efficient conversion
        return [RunLogResponse.model_validate(log) for log in db_logs]

    async def get_running_fitness_score(self, user_id: int) -> Dict[str, Any]:
        """
        Calculates the user's running fitness score using a weighted rolling average
        of their best pace over the last 90 days.
        """
        # Fetch raw ORM objects from the database
        logs = await self.repository.get_user_run_history_raw(user_id)
        if not logs:
            return {"fitness_score": 0.0,
                    "message": "No running data available to calculate fitness score."}

        # 1. Convert ORM objects to a Pandas DataFrame for time-series analysis
        data = [
            {
                'log_date': log.log_date,
                'pace': self.calculate_pace(log.distance_km, log.duration_min)
            } for log in logs
        ]
        df = pd.DataFrame(data)

        # 2. Set 'log_date' as index and filter by time window (last 90 days)
        df['log_date'] = pd.to_datetime(df['log_date'])
        df = df.set_index('log_date')

        # Filter for runs within the last 90 days to avoid stale data impact
        start_date = datetime.now() - timedelta(days=90)
        df_recent = df[df.index >= start_date].copy()

        if df_recent.empty:
            return {"fitness_score": 0.0,
                    "message": "No running data available in the last 90 days."}

        # 3. Calculate Daily Best Pace (Uses the minimum pace, as lower = faster/better)
        daily_best_pace = df_recent['pace'].resample('D').min().dropna()

        # 4. Calculate Rolling Average
        # 7-day rolling mean smooths out daily variance and provides a robust metric.
        rolling_pace = daily_best_pace.rolling(window=7, min_periods=1,
                                               center=False).mean()

        # Get the latest calculated rolling pace value (the user's current 'smoothed' pace)
        current_pace_metric = rolling_pace.iloc[-1]

        # 5. Transform Pace (Lower is Better) into a Score (Higher is Better)
        # We create a 0-100 scale: 7:00/km -> 0, 3:00/km -> 100

        SLOW_PACE_BOUND = 7.0  # 7:00 min/km (target for 0 score)
        FAST_PACE_BOUND = 3.0  # 3:00 min/km (target for 100 score)
        PACE_RANGE = SLOW_PACE_BOUND - FAST_PACE_BOUND

        # Clip the pace metric to ensure the score is always between 0 and 100 (or slightly above/below)
        pace_to_score = max(FAST_PACE_BOUND, min(SLOW_PACE_BOUND, current_pace_metric))

        # Scoring Formula: maps the pace inversely to the 0-100 scale
        fitness_score = ((SLOW_PACE_BOUND - pace_to_score) / PACE_RANGE) * 100

        final_score = round(fitness_score, 1)

        return {
            "fitness_score": final_score,
            "latest_pace_metric": round(current_pace_metric, 2),
            "message": f"Based on your 7-day rolling best pace of {round(current_pace_metric, 2)} min/km (calculated from the last 90 days), your Running Fitness Score is {final_score}/100."
        }