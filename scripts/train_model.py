import os
import sys

# Add the 'src' directory to the Python path so we can import modules from it
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import the refactored functions
from src.data_loader import load_and_prepare_data_for_goal_prediction
from src.model_trainer import train_and_save_model

if __name__ == "__main__":
    print("Starting model training using modular architecture...")

    # 1. Load Data
    features, target = load_and_prepare_data_for_goal_prediction()

    # 2. Train and Save Model
    train_and_save_model(features, target)