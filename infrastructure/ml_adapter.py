import joblib
import pandas as pd
import os

#  Configuration (Relative path adjustment for running from main.py)
# NOTE: The path is relative to the project root, which is the running directory.
MODEL_FILE_PATH = 'models/workout_recommender_pipeline_goal.joblib'
MODEL = None


#  Model Loading (Updated for FastAPI Lifespan)

def load_model():
    """Loads the model pipeline."""
    global MODEL
    if MODEL is None:
        if not os.path.exists(MODEL_FILE_PATH):
            print(
                f"Model file not found at {MODEL_FILE_PATH}. Please run the training script first.")
            # Do NOT raise FileNotFoundError here; let FastAPI start, but mark model as unloaded
            return None

        print(f" Loading model from {MODEL_FILE_PATH}...")
        MODEL = joblib.load(MODEL_FILE_PATH)
        print(" Model loaded successfully.")
    return MODEL


def preprocess_input(workout_type, equipment, intensity, duration_min, calories_burned):
    """
    Applies the exact preprocessing steps the model was trained on.
    """
    input_data = pd.DataFrame([{
        'workout_type': workout_type,
        'equipment': equipment,
        'intensity': intensity,
        'duration_min': duration_min,
        'calories_burned': calories_burned,
    }])

    intensity_map = {'very_low': 1, 'low': 2, 'moderate': 3, 'high': 4}
    input_data['intensity_numeric'] = input_data['intensity'].map(intensity_map)
    input_data = input_data.drop(columns=['intensity'])

    features = input_data[
        ['workout_type', 'equipment', 'duration_min', 'calories_burned',
         'intensity_numeric']
    ]

    return features


def predict_goal(workout_type, equipment, intensity, duration_min, calories_burned):
    """Makes a prediction using the loaded pipeline."""
    pipeline = load_model()

    if pipeline is None:
        raise Exception("ML Model is not loaded. Cannot make prediction.")

    processed_input = preprocess_input(workout_type, equipment, intensity, duration_min,
                                       calories_burned)

    prediction = pipeline.predict(processed_input)

    return prediction[0]
