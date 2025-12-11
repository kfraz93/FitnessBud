import os
import sys
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from numpy import sqrt

# Ensure the script can locate relative paths for models/
# NOTE: This sys.path line is often required when running scripts outside the main app context.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- Constants ---
MODEL_FILE = "models/running_pace_predictor.joblib"
DATA_FILE = "models/strava_data.xlsx"


def train_and_save_pace_model():
    """
    Trains a Random Forest Regressor model using the optimal features and saves the pipeline.
    This function contains the full ML pipeline logic and should only be run offline.
    """
    # 1. Load Data
    try:
        data = pd.read_excel(DATA_FILE, sheet_name="Sheet1")
    except FileNotFoundError:
        print(
            f"CRITICAL ERROR: Strava running data Excel file not found at {DATA_FILE} for training.")
        return

    # 2. DATA FILTERING: Filter ONLY for 'Run'
    data = data[data['sport_type'] == 'Run'].copy()

    # 3. Feature Engineering: Create Target and Base Features
    data['distance_km'] = data['distance_km'] / 1000
    data['duration_min'] = data['duration_min'] / 60

    epsilon = 1e-6
    data['pace_min_per_km'] = data['duration_min'] / (data['distance_km'] + epsilon)

    # 4. OUTLIER REMOVAL
    data = data[
        (data['pace_min_per_km'] >= 3.0) & (data['pace_min_per_km'] <= 12.0)
        ].copy()

    # 5. FEATURE ENGINEERING: Calculate Rolling Average Pace (The Key Feature)
    data = data.sort_values(by='start_date_local')

    # Using the confirmed optimal window size: 4
    OPTIMAL_WINDOW = 4
    # shift(1) ensures we use the average UP TO THE PREVIOUS RUN
    data['rolling_avg_pace'] = data['pace_min_per_km'].shift(1).rolling(
        window=OPTIMAL_WINDOW, min_periods=1).mean()

    # Drop the first few rows where rolling_avg_pace is based on limited data
    # (though min_periods=1 handles it, we want a clean feature set)
    data = data.dropna(subset=['rolling_avg_pace'])

    # 6. Define Features and Target
    FEATURES = ['distance_km', 'rolling_avg_pace']
    TARGET = 'pace_min_per_km'

    # Handle missing/infinite values (robustness check)
    X = data[FEATURES].fillna(0).replace([np.inf, -np.inf], np.nan).fillna(0)
    y = data[TARGET].replace([np.inf, -np.inf], np.nan).fillna(data[TARGET].mean())

    # Final cleanup (just in case)
    clean_data = X.copy()
    clean_data[TARGET] = y
    clean_data.dropna(inplace=True)
    X = clean_data[FEATURES]
    y = clean_data[TARGET]

    # Ensure there are enough samples left
    if len(X) < 10:
        print("ERROR: Insufficient clean data remaining for training.")
        return

    # 7. Split Data, Train, and Evaluate
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2,
                                                        random_state=42)

    # Instantiate the Random Forest Regressor (The final production model)
    pace_model = RandomForestRegressor(n_estimators=100, random_state=42)
    pace_model.fit(X_train, y_train)

    # Evaluation
    y_pred = pace_model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    rmse = sqrt(mean_squared_error(y_test, y_pred))

    print("\n--- Final Model Performance Metrics (Random Forest) ---")
    print(f"Trained with Optimal Window Size: {OPTIMAL_WINDOW}")
    print(f"Test Set R-squared (R2) Score: {r2:.4f}")
    print(f"Test Set Root Mean Squared Error (RMSE): {rmse:.4f} min/km")
    print("-------------------------------------------------------\n")

    # 8. Save Model
    os.makedirs(os.path.dirname(MODEL_FILE), exist_ok=True)
    joblib.dump(pace_model, MODEL_FILE)
    print(f"Pace Prediction Model trained and saved to {MODEL_FILE}")


if __name__ == "__main__":
    print("Starting Running Pace Model training (Dedicated Script)...")
    train_and_save_pace_model()
    print("Running Pace Model training complete.")