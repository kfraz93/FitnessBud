import joblib
import os
import pandas as pd
from typing import Optional, Any
import numpy as np


MODEL_FILE = "models/running_pace_predictor.joblib"

# Use 'Any' for model type hint since it can be any scikit-learn estimator
# We initialize it to None
pace_model: Optional[Any] = None


def load_pace_model():
    """
    Loads the trained pace prediction model from disk.
    If the model is not found, it prints a critical warning and pace_model remains None,
    which triggers the default fallback pace in predict_pace().
    """
    global pace_model
    try:
        if os.path.exists(MODEL_FILE):
            pace_model = joblib.load(MODEL_FILE)
            print("ML Pace Prediction Model loaded successfully.")
        else:
            print(
                f"CRITICAL WARNING: Pace Prediction Model file not found at {MODEL_FILE}.")
            print("Pace prediction will use the default fallback value (5.5 min/km).")
    except Exception as e:
        print(f"ERROR: Failed to load pace model from {MODEL_FILE}: {e}")
        pace_model = None  # Ensure it is None on failure


def predict_pace(distance_km: float, rolling_avg_pace: float) -> float:
    """
    Adapter method. Predicts the optimal pace (min/km) using the loaded ML model.
    This is the production interface for the RunningService.

    :param distance_km: The distance of the run to predict the pace for.
    :param rolling_avg_pace: The runner's current fitness (rolling average pace).
    :return: The predicted pace in minutes per kilometer.
    """
    global pace_model
    # 1. Fallback if model is not loaded
    if pace_model is None:
        return 5.5

    # 2. Prepare features for prediction
    # Features must match the trained model: distance_km and rolling_avg_pace
    # We use a DataFrame as that is what scikit-learn expects
    features = pd.DataFrame([[distance_km, rolling_avg_pace]],
                            columns=['distance_km', 'rolling_avg_pace'])

    # 3. Handle potential NaN/Inf values (safety)
    features = features.replace([np.inf, -np.inf], np.nan).fillna(0)

    # 4. Perform Prediction
    try:
        predicted_pace = pace_model.predict(features)[0]
    except Exception as e:
        print(f"ML Prediction Error: {e}. Returning default pace.")
        return 5.5

    # 5. Apply reasonable bounds (Safety check against extreme predictions)
    # Pace should be between 3.0 min/km (very fast) and 10.0 min/km (slow jog/walk)
    if predicted_pace < 3.0 or predicted_pace > 10.0:
        return 5.5  # Fallback to default if prediction is extreme

    return float(predicted_pace)


# CRITICAL: Load the model on startup when the module is imported by FastAPI
load_pace_model()