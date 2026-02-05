from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from api.v1.endpoints import auth
# 1. Import the new routers from the endpoints directory
from api.v1.endpoints import users
from api.v1.endpoints import workout_logs
from api.v1.endpoints import running_logs  # <-- NEW: Import the running logs router

# Local imports
from core.config import settings
from infrastructure.db import create_db_and_tables

# ML Adapters
from infrastructure.ml_workout_adapter import \
    load_model as load_workout_model  # <-- Renamed for clarity
from infrastructure.ml_workout_adapter import predict_goal
from infrastructure import \
    ml_running_adapter

# Define valid workout types (based on your limited training data)
VALID_WORKOUT_TYPES = ["deadlift", "running", "bench_press", "yoga", "cycling"]


@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    Handles startup and shutdown events for the FastAPI application.
    Ensures the database tables are created on startup and models are loaded.
    """
    # --- On Application Startup ---
    print("Application startup: Creating database tables...")
    await create_db_and_tables()
    print("Application startup: Database tables created successfully.")

    # Load both ML models during startup (Lifespan Hook)
    print("Application startup: Loading ML Models...")
    load_workout_model()  # Workout Model
    ml_running_adapter.load_model()  # <-- NEW: Running Pace Model

    yield  # The application runs here

    # --- On Application Shutdown ---
    print("Application shutdown complete.")


# Initialize the main FastAPI application instance
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="AI-Powered Workout Recommendation System Backend.",
    lifespan=lifespan  # Attach the lifespan manager
)

# 2. Include the Routers with a /v1 prefix for versioning
app.include_router(users.router, prefix="/v1")
app.include_router(auth.router, prefix="/v1")
app.include_router(workout_logs.router, prefix="/v1")
app.include_router(running_logs.router,
                   prefix="/v1")  # <-- NEW: Include the running logs router


# Root endpoint for basic verification
@app.get("/info")
async def root():
    return {"message": f"Welcome to {settings.APP_NAME}."}


# --- Configure Templates and Static Files ---
# Mount the static directory to serve CSS/JS
# app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure the Jinja2 template directory
templates = Jinja2Templates(directory="templates")


# --- Recommendation Logic Endpoint (for the form submission) ---

@app.get("/", response_class=HTMLResponse)
async def get_recommendation_form(request: Request):
    """Serves the main recommendation form page."""
    valid_equipment = ["full_gym", "home_gym", "yoga_mat", "none"]
    valid_intensity = ["very_low", "low", "moderate", "high"]

    return templates.TemplateResponse(
        "recommend.html",
        {"request": request, "equipment_options": valid_equipment,
         "intensity_options": valid_intensity,
         "workout_type_options": VALID_WORKOUT_TYPES,
         "result": None}
    )


@app.post("/recommend", response_class=HTMLResponse)
async def post_recommendation(
        request: Request,
        workout_type: str = Form(...),
        equipment: str = Form(...),
        intensity: str = Form(...),
        duration_min: int = Form(...),
        calories_burned: float = Form(...)
):
    """Handles the form submission and returns the predicted goal."""

    # 1. Input Validation (CRITICAL STEP FOR USABILITY)
    valid_equipment = ["full_gym", "home_gym", "yoga_mat", "none"]
    valid_intensity = ["very_low", "low", "moderate", "high"]
    valid_workout_types = VALID_WORKOUT_TYPES

    if (equipment not in valid_equipment or intensity not in valid_intensity or
            workout_type not in valid_workout_types):
        error_message = "Invalid selection for workout type, equipment, or intensity."
        return templates.TemplateResponse(
            "recommend.html",
            {"request": request, "error": error_message,
             "equipment_options": valid_equipment, "intensity_options": valid_intensity,
             "workout_type_options": valid_workout_types,
             "result": None}
        )

    # 2. Call your ML Service
    try:
        predicted_goal = predict_goal(workout_type, equipment, intensity, duration_min,
                                      calories_burned)
        result = f"Input: {workout_type}, {equipment} -> Predicted Goal: {predicted_goal}"
    except Exception as e:
        # Catch exception if model failed to load
        result = f"Prediction Error: {e}"

    # 3. Render the page with the result
    return templates.TemplateResponse(
        "recommend.html",
        {"request": request,
         "equipment_options": valid_equipment,
         "intensity_options": valid_intensity,
         "workout_type_options": valid_workout_types,
         # PASS SUBMITTED VALUES BACK TO THE TEMPLATE CONTEXT:
         "workout_type": workout_type,
         "equipment": equipment,
         "intensity": intensity,
         "duration_min": duration_min,
         "calories_burned": calories_burned,
         "result": result}
    )