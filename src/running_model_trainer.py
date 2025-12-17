import joblib
import pandas as pd
import numpy as np
import os
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error  # Added metrics

MODEL_FILE_PATH = "models/running_pace_predictor.joblib"


def train_and_save_pace_model(data_file: str):
    try:
        data = pd.read_excel(data_file, sheet_name="Sheet1")
    except Exception as e:
        print(f"CRITICAL ERROR: Could not read {data_file}: {e}")
        return

    # 2. Filter for Runs
    if 'sport_type' in data.columns:
        data = data[data['sport_type'] == 'Run'].copy()

    # 3. Defensive Column Mapping
    try:
        if 'distance' in data.columns:
            data['distance_km'] = data['distance'] / 1000
        elif 'distance_km' in data.columns:
            if data['distance_km'].max() > 500:
                data['distance_km'] = data['distance_km'] / 1000
        else:
            print(f"ERROR: Missing distance column. Available: {data.columns.tolist()}")
            return

        if 'moving_time' in data.columns:
            data['duration_min'] = data['moving_time'] / 60
        elif 'elapsed_time' in data.columns:
            data['duration_min'] = data['elapsed_time'] / 60
        else:
            print(f"ERROR: Missing time column. Available: {data.columns.tolist()}")
            return

        epsilon = 1e-6
        data['pace_min_per_km'] = data['duration_min'] / (data['distance_km'] + epsilon)

    except Exception as e:
        print(f"Unexpected Mapping Error: {e}")
        return

    # 4. Outlier Removal
    data = data[
        (data['pace_min_per_km'] >= 3.0) & (data['pace_min_per_km'] <= 12.0)].copy()

    # 5. Rolling Average
    date_col = 'start_date_local' if 'start_date_local' in data.columns else \
    data.columns[0]
    data = data.sort_values(by=date_col)

    OPTIMAL_WINDOW = 4
    data['rolling_avg_pace'] = data['pace_min_per_km'].shift(1).rolling(
        window=OPTIMAL_WINDOW, min_periods=1).mean()

    data = data.dropna(subset=['rolling_avg_pace'])

    # 6. Train/Test Split
    FEATURES = ['distance_km', 'rolling_avg_pace']
    TARGET = 'pace_min_per_km'

    X = data[FEATURES].fillna(0).replace([np.inf, -np.inf], np.nan).fillna(0)
    y = data[TARGET].replace([np.inf, -np.inf], np.nan).fillna(data[TARGET].mean())

    if len(X) < 5:
        print("ERROR: Not enough samples for training.")
        return

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2,
                                                        random_state=42)

    # 7. Model Training
    pace_model = RandomForestRegressor(n_estimators=100, random_state=42)
    pace_model.fit(X_train, y_train)

    # --- 8. EVALUATION (New Section) ---
    y_pred = pace_model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)

    print("Running Pace Model trained successfully.")
    print(f"   R-squared Score: {r2:.4f}")
    print(f"   Mean Absolute Error: {mae:.4f} min/km")

    # 9. Save
    os.makedirs(os.path.dirname(MODEL_FILE_PATH), exist_ok=True)
    joblib.dump(pace_model, MODEL_FILE_PATH)
    print(f"💾 Pace Prediction Model saved to {MODEL_FILE_PATH}")