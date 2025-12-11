import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeClassifier

# Define the location where the model pipeline will be saved
MODEL_FILE_PATH = 'models/workout_recommender_pipeline_goal.joblib'


def build_preprocessor(features_dataframe):
    """
    Creates a ColumnTransformer to apply different preprocessing steps
    to numerical and categorical columns, matching the Goal Prediction model.
    """

    numerical_features = ['duration_min', 'calories_burned', 'intensity_numeric']
    categorical_features = ['workout_type', 'equipment']

    preprocessor = ColumnTransformer(
        transformers=[
            # Scale numerical data
            ('standard_scaler', StandardScaler(), numerical_features),

            # One-Hot Encode categorical data
            ('one_hot_encoder',
             OneHotEncoder(handle_unknown='ignore', sparse_output=False),
             categorical_features)
        ],
        remainder='drop'
    )

    return preprocessor


def train_and_save_model(all_features, target_variable):
    """Trains the model pipeline and saves it to joblib file."""

    # Split data for validation (80% training, 20% testing)
    training_features, testing_features, training_targets, testing_targets = train_test_split(
        all_features, target_variable, test_size=0.2, random_state=42
    )

    # Build the complete pipeline: Preprocessing -> Model
    preprocessor = build_preprocessor(training_features)

    model_pipeline = Pipeline(steps=[
        ('data_preprocessor', preprocessor),
        ('classifier', DecisionTreeClassifier(random_state=42))
    ])

    # Train the model (FIT)
    model_pipeline.fit(training_features, training_targets)

    # Evaluate performance
    accuracy = model_pipeline.score(testing_features, testing_targets)
    print("Model trained successfully.")
    print(f"   Accuracy on test set: {accuracy:.4f}")

    # Save the entire pipeline (preprocessor + model) to a file
    joblib.dump(model_pipeline, MODEL_FILE_PATH)
    print(f"💾 Model pipeline saved to {MODEL_FILE_PATH}")