import joblib
import os
import pandas as pd
from typing import Optional, Any
import numpy as np

# Configuration (Consistent naming)
MODEL_FILE_PATH = "models/running_pace_predictor.joblib"
MODEL: Optional[Any] = None  # Use the consistent MODEL name


# --- Model Loading (Updated for FastAPI Lifespan) ---

def load_model():
    """
    Loads the trained pace prediction model from disk.
    This function is intended to be called during FastAPI startup/lifespan.
    """
    global MODEL
    if MODEL is None:
        if not os.path.exists(MODEL_FILE_PATH):
            print(
                f"Model file not found at {MODEL_FILE_PATH}. Please run the training script for running app first.")
            # Do NOT raise FileNotFoundError here; return None to signal failure
            return None

        try:
            print(f" Loading running pace model from {MODEL_FILE_PATH}...")
            MODEL = joblib.load(MODEL_FILE_PATH)
            print(" Running Pace Model loaded successfully.")
        except Exception as e:
            print(f"ERROR: Failed to load pace model from {MODEL_FILE_PATH}: {e}")
            MODEL = None  # Ensure it is None on failure

    return MODEL


# --- Prediction Interface ---

def predict_pace(distance_km: float, rolling_avg_pace: float) -> float:
    """
    Adapter method. Predicts the optimal pace (min/km) using the loaded ML model.
    """
    pipeline = load_model()

    if pipeline is None:
        # Match the workout adapter's error handling for consistency
        raise Exception("ML Running Pace Model is not loaded. Cannot make prediction.")

    # 1. Prepare features for prediction
    # Features must match the trained model: distance_km and rolling_avg_pace
    features = pd.DataFrame([[distance_km, rolling_avg_pace]],
                            columns=['distance_km', 'rolling_avg_pace'])

    # 2. Handle potential NaN/Inf values (safety)
    features = features.replace([np.inf, -np.inf], np.nan).fillna(0)

    # 3. Perform Prediction
    try:
        predicted_pace = pipeline.predict(features)[0]
    except Exception as e:
        print(f"ML Prediction Error: {e}. Raising exception.")
        # If prediction fails, treat it as a critical error (500)
        raise Exception(f"ML Prediction failed: {e}")

    # 4. Apply reasonable bounds (Safety check against extreme predictions)
    # Pace should be between 3.0 min/km (very fast) and 10.0 min/km (slow jog/walk)
    if predicted_pace < 3.0 or predicted_pace > 10.0:
        print(
            f"WARNING: Predicted pace {predicted_pace:.2f} is outside reasonable bounds. Using default.")
        return 5.5  # Fallback to default if prediction is extreme

    return float(predicted_pace)
