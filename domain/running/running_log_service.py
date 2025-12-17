from fastapi import HTTPException
from fastapi import status

# Third-party library for feature calculation
import pandas as pd

# Domain Layer Imports (using consistent shared schemas and ORM model)
from domain.shared.schemas import RunningLogCreate
from domain.shared.schemas import RunningLogUpdate
from infrastructure.orm_models import \
    RunningLog  # Assuming the ORM model is named RunningLog
from infrastructure.running.running_log_repository import \
    RunningLogRepository  # RENAMED REPO
from infrastructure import ml_running_adapter  # Imports the ML PORT/ADAPTER


class RunningLogService:
    """
    Handles all business logic and coordination for running logs.
    Ensures data consistency, user ownership, and handles ML feature engineering.
    """

    def __init__(self, repository: RunningLogRepository):
        # Store the repository instance passed to the constructor
        self.repository = repository

    # --- CRUD Operations (Matching WorkoutLogService) ---

    async def create_log(self, log_in: RunningLogCreate, user_id: int) -> RunningLog:
        """Creates a new running log and commits the transaction."""

        # Persistence call
        db_log = await self.repository.create(log_in=log_in, user_id=user_id)

        # Commit the transaction after successful creation
        await self.repository.db.commit()

        return db_log

    async def get_log_by_id(self, log_id: int, user_id: int) -> RunningLog:
        """Fetches a single log, ensuring it belongs to the user."""
        db_log = await self.repository.get_by_id(log_id=log_id, user_id=user_id)

        if not db_log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Running log not found or access denied."
            )
        return db_log

    async def get_all_logs_by_user(self, user_id: int) -> list[RunningLog]:
        """Fetches all logs for a user."""
        return await self.repository.get_all_by_user(user_id=user_id)

    async def update_log(self, log_id: int, user_id: int,
                         log_update: RunningLogUpdate) -> RunningLog:
        """Updates an existing log for a specific user and commits."""

        # Persistence call
        db_log = await self.repository.update(
            log_id=log_id,
            user_id=user_id,
            log_update=log_update
        )

        if not db_log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Running log not found or access denied."
            )

        # Commit the transaction
        await self.repository.db.commit()

        return db_log

    async def delete_log(self, log_id: int, user_id: int) -> None:
        """Deletes a log for a specific user and commits."""

        # Persistence call
        deleted = await self.repository.delete(log_id=log_id, user_id=user_id)

        if not deleted:
            # Note: We check for not deleted and raise 404, providing a clean response
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Running log not found or access denied."
            )

        # Commit the transaction after successful deletion
        await self.repository.db.commit()

    # --- ML Prediction Logic (Business Logic) ---

    async def predict_recommended_pace(self, user_id: int, distance_km: float) -> float:
        """
        Predicts the recommended pace by fetching user history, calculating the
        rolling average pace feature, and calling the ML adapter.
        """
        # 1. Fetch user's historical data (Using raw method which we will define)
        # We need raw ORM objects/dicts for accurate feature calculation
        raw_logs = await self.repository.get_all_by_user_raw(
            user_id)  # Renamed for consistency

        if not raw_logs:
            # Not enough data for prediction. Use a safe default.
            return 5.5

        # 2. Convert historical data to a DataFrame for time-series feature calculation
        data = pd.DataFrame([
            {
                # Ensure these attributes match the ORM model we define later
                'distance_km': log.distance_km,
                'duration_min': log.duration_min,
                'running_date': log.running_date
            }
            for log in raw_logs
        ])

        # 3. Calculate Base Pace and Rolling Average Feature (Business Logic)
        data['pace_min_per_km'] = data['duration_min'] / (
            data['distance_km'].replace(0, 1e-6))

        # Sort by date (CRITICAL for rolling average) - Ensure column name is consistent
        data = data.sort_values(by='running_date')

        OPTIMAL_WINDOW = 4

        # Calculate the rolling average of the *previous* 4 runs
        data['rolling_avg_pace'] = data['pace_min_per_km'].shift(1).rolling(
            window=OPTIMAL_WINDOW,
            min_periods=1
        ).mean()

        current_rolling_avg_pace = data['rolling_avg_pace'].iloc[-1]

        if pd.isna(current_rolling_avg_pace):
            # Fallback if there are fewer runs than the window size
            current_rolling_avg_pace = data['pace_min_per_km'].mean()

        # 4. Call the ML Adapter (Delegation to the Infrastructure Layer)
        recommended_pace = ml_running_adapter.predict_pace(
            distance_km=distance_km,
            rolling_avg_pace=current_rolling_avg_pace
        )

        return recommended_pace
