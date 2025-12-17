import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import the refactored functions
from src.data_loader import load_and_prepare_data_for_goal_prediction
from src.data_loader import get_running_data_file_path

from src.workout_model_trainer import train_and_save_model
from src.running_model_trainer import train_and_save_pace_model

if __name__ == "__main__":
    print("Starting ML Model Training for FitnessBud...")

    # --- 1. WORKOUT GOAL PREDICTION MODEL ---
    print("\n--- Training Workout Goal Predictor ---")
    try:
        # 1.1 Load Data
        workout_features, workout_target = load_and_prepare_data_for_goal_prediction()

        # 1.2 Train and Save Model
        train_and_save_model(workout_features, workout_target)
        print("Workout Goal Predictor saved successfully.")
    except Exception as e:
        print(f"ERROR training Workout Goal Predictor: {e}")

    # --- 2. RUNNING PACE PREDICTION MODEL ---
    print("\n--- Training Running Pace Predictor ---")
    try:
        # 2.1 Get Data File Path
        data_file_path = get_running_data_file_path()  # e.g., returns "models/strava_data.xlsx"

        # 2.2 Train and Save Model
        train_and_save_pace_model(data_file_path)
        print("Running Pace Predictor saved successfully.")
    except Exception as e:
        print(f"ERROR training Running Pace Predictor: {e}")

    print("\nAll model training attempts completed.")
