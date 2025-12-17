import os

import pandas as pd

DATA_FILE_PATH = 'models/synthetic_workout_data.csv'


def load_and_prepare_data_for_goal_prediction():
    """
    Loads the synthetic data and prepares features and target specifically
    for the Goal Prediction model (Workout Log -> User Goal).

    Features: ['workout_type', 'equipment', 'intensity', 'duration_min', 'calories_burned']
    Target: ['goal']
    """
    if not os.path.exists(DATA_FILE_PATH):
        raise FileNotFoundError(
            f"Data file not found at {DATA_FILE_PATH}. Please run generate_data.py first."
        )

    data_frame = pd.read_csv(DATA_FILE_PATH)

    # 1. Define Target and Features
    target_variable = data_frame['goal']

    all_features = data_frame[
        ['workout_type', 'equipment', 'intensity', 'duration_min', 'calories_burned']
    ].copy()

    # 2. Ordinally encode intensity (Must match the training logic)
    intensity_map = {'very_low': 1, 'low': 2, 'moderate': 3, 'high': 4}
    all_features['intensity_numeric'] = all_features['intensity'].map(intensity_map)
    all_features = all_features.drop(columns=['intensity'])

    return all_features, target_variable

def get_running_data_file_path() -> str:
    """
    Returns the file path for the raw running data used to train the pace predictor.
    This path should be relative to the project root when the script is run.
    """
    # NOTE: This path is hardcoded based on the assumed location of your training data file.
    return "models/strava_data.xlsx"