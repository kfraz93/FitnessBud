from typing import List
from domain.running import running_schemas
from infrastructure.running.running_repository import RunningRepository
from infrastructure.running import running_ml_adapter  # Imports the ML PORT/ADAPTER

import pandas as pd  # Required for feature calculation (time-series rolling average)


class RunningService:
    """
    Domain Service: Implements business logic for the Running App (Port implementation).
    """

    def __init__(self, repository: RunningRepository):
        self.repository = repository

    async def log_run(self, user_id: int,
                      log_data: running_schemas.RunLogCreate) -> running_schemas.RunLogResponse:
        """Logs a new run and returns the calculated pace."""
        db_log = await self.repository.create_run_log(user_id, log_data)

        return running_schemas.RunLogResponse.model_validate(db_log)

    async def get_user_run_history(self, user_id: int) -> List[
        running_schemas.RunLogResponse]:
        """Retrieves a user's run history."""
        db_logs = await self.repository.get_run_logs_by_user(user_id)
        return [running_schemas.RunLogResponse.model_validate(log) for log in db_logs]

    async def predict_recommended_pace(self, user_id: int, distance_km: float) -> float:
        """
        Predicts the recommended pace by fetching user history, calculating the
        rolling average pace feature, and calling the ML adapter.
        """
        # 1. Fetch user's historical data (Adapter/Repository Call)
        # We need raw ORM objects/dicts for accurate feature calculation
        raw_logs = await self.repository.get_user_run_history_raw(user_id)

        if not raw_logs:
            # Not enough data for prediction. Use a safe default.
            return 5.5

        # 2. Convert historical data to a DataFrame for time-series feature calculation
        # Data is extracted using log.log_date, log.distance_km, and log.duration_min
        data = pd.DataFrame([
            {
                'distance_km': log.distance_km,
                'duration_min': log.duration_min,
                'log_date': log.log_date
            }
            for log in raw_logs
        ])

        # 3. Calculate Base Pace and Rolling Average Feature (Business Logic)

        # NOTE: Removed unnecessary conversions. We assume distance_km is already in km
        # and duration_min is already in minutes, matching the column names.

        # Calculate pace, handle zero distance with epsilon
        data['pace_min_per_km'] = data['duration_min'] / (
            data['distance_km'].replace(0, 1e-6))

        # Sort by date (CRITICAL) - FIXED to use 'log_date' column name
        data = data.sort_values(by='log_date')

        # Optimal window size found during tuning: 4
        OPTIMAL_WINDOW = 4

        # Calculate the rolling average of the *previous* 4 runs
        data['rolling_avg_pace'] = data['pace_min_per_km'].shift(1).rolling(
            window=OPTIMAL_WINDOW,
            min_periods=1
        ).mean()

        # The last calculated rolling average is the proxy for the user's current fitness
        current_rolling_avg_pace = data['rolling_avg_pace'].iloc[-1]

        if pd.isna(current_rolling_avg_pace):
            # Fallback if there are fewer runs than the window size
            current_rolling_avg_pace = data['pace_min_per_km'].mean()

        # 4. Call the ML Adapter (Delegation to the Infrastructure Layer)
        recommended_pace = running_ml_adapter.predict_pace(
            distance_km=distance_km,
            rolling_avg_pace=current_rolling_avg_pace
        )

        return recommended_pace
