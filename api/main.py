from fastapi import FastAPI, Form, Request, Depends, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import json
from urllib.parse import quote_plus, unquote_plus

# Local imports
from core.config import settings
from infrastructure.db import create_db_and_tables, get_db_session

# Import specific router instances directly from their files (NOT the modules)
from api.v1.endpoints.users import user_router as users_router
from api.v1.endpoints.auth import auth_router as auth_router
from api.v1.endpoints.workout_logs import router as workout_logs_router
from api.v1.endpoints.running_logs import router as running_logs_router

from infrastructure.ml_adapter import load_model, predict_goal
from infrastructure.running.running_ml_adapter import load_pace_model

# Must be imported so SQLAlchemy models are registered before create_db_and_tables is called.
import domain.running.running_models

from domain.running.running_schemas import RunLogResponse, RunLogCreate
from application.running.running_service import RunningService
from infrastructure.running.running_repository import RunningRepository
from api.deps import get_current_user
from domain.user.user_schemas import UserOut

# Define valid workout types (based on your limited training data)
VALID_WORKOUT_TYPES = ["deadlift", "running", "bench_press", "yoga", "cycling"]


@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    Handles startup and shutdown events for the FastAPI application.
    Ensures the database tables are created and ML models are loaded on startup.
    """
    # --- On Application Startup ---
    print("Application startup: Creating database tables...")
    await create_db_and_tables()
    print("Application startup: Database tables created successfully.")

    # Load machine learning models into memory
    load_model()
    load_pace_model()
    print("Application startup: ML models loaded.")

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

# CORS Middleware setup (Allows all origins for local development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Include the Routers with a /v1 prefix for versioning
# We now include the specific router objects, not the modules.
# We include the auth router first since it defines /v1/auth/token for login.
app.include_router(auth_router, prefix="/v1")
app.include_router(users_router, prefix="/v1")
app.include_router(workout_logs_router, prefix="/v1")
app.include_router(running_logs_router, prefix="/v1")


# Root endpoint for basic verification
@app.get("/info")
async def root():
    return {"message": f"Welcome to {settings.APP_NAME}."}


# --- Configure Templates and Static Files ---
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# Dependency Injector for RunningService (reused from running_logs.py)
def get_running_service(
        db_session: AsyncSession = Depends(get_db_session)) -> RunningService:
    """Provides a RunningService instance with a repository bound to the current session."""
    repository = RunningRepository(session=db_session)
    return RunningService(repository=repository)


@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request, error: Optional[str] = Query(None)):
    """Serves the login/register page. This is the new application entry point."""
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": error}
    )

# --- Recommendation Logic Endpoint (Central View Manager) ---

@app.get("/recommend", response_class=HTMLResponse)
async def get_recommendation_form(
        request: Request,
        current_user: UserOut = Depends(get_current_user),
        service: RunningService = Depends(get_running_service),
        # New query parameters for view state management (HTML only)
        view: str = Query('log-run'),  # Default view
        log_status: Optional[str] = Query(None),
        prediction_result: Optional[str] = Query(None),  # JSON string result
        running_error: Optional[str] = Query(None)  # URL-encoded error message
):
    """
    Serves the main recommendation form page.
    Handles view switching and displays status messages/results based on query parameters.
    """
    valid_equipment = ["full_gym", "home_gym", "yoga_mat", "none"]
    valid_intensity = ["very_low", "low", "moderate", "high"]

    # --- Running Hub Logic ---
    run_history: List[RunLogResponse] = []
    running_prediction_result = None

    # Try to decode error messages
    if running_error:
        running_error = unquote_plus(running_error)

    # Fetch user's running history for display regardless of the current view
    try:
        run_history = await service.get_user_run_history(current_user.id)
    except Exception as e:
        # If DB read fails, set a history error
        running_error = f"Failed to load run history: {e}"

    # Handle prediction result passed back via query param
    if prediction_result:
        try:
            # Decode the URL-encoded JSON string
            decoded_json = unquote_plus(prediction_result)
            running_prediction_result = json.loads(decoded_json)
        except (json.JSONDecodeError, Exception):
            running_error = "Error decoding prediction result."
            prediction_result = None

    # Set the current view (must be one of the known views)
    known_views = ['log-run', 'view-history', 'predict-run']
    current_view = view if view in known_views else 'log-run'

    return templates.TemplateResponse(
        "recommend.html",
        {"request": request,
         "equipment_options": valid_equipment,
         "intensity_options": valid_intensity,
         "workout_type_options": VALID_WORKOUT_TYPES,
         "current_user": current_user,
         "run_history": run_history,
         "result": None,
         # New context for HTML-only view switching:
         "current_view": current_view,
         "log_status": log_status,
         "running_prediction_result": running_prediction_result,
         "running_error": running_error
         }
    )


@app.post("/recommend", response_class=HTMLResponse)
async def post_recommendation(
        request: Request,
        workout_type: str = Form(...),
        equipment: str = Form(...),
        intensity: str = Form(...),
        duration_min: int = Form(...),
        calories_burned: float = Form(...),
        current_view: str = Form('log-run'),  # Hidden field to keep running hub context
        current_user: UserOut = Depends(get_current_user),
        service: RunningService = Depends(get_running_service)
):
    """
    Handles the workout goal form submission, returns the predicted goal,
    and re-renders the page, maintaining the current_view context.
    """

    # 1. Input Validation
    valid_equipment = ["full_gym", "home_gym", "yoga_mat", "none"]
    valid_intensity = ["very_low", "low", "moderate", "high"]
    valid_workout_types = VALID_WORKOUT_TYPES
    error_message = None
    result = None  # <-- FIX: Initialize result to None

    if (equipment not in valid_equipment or intensity not in valid_intensity or
            workout_type not in valid_workout_types):
        error_message = "Invalid selection for workout type, equipment, or intensity."

    # 2. Call ML Prediction
    predicted_goal = None
    if not error_message:
        try:
            predicted_goal = predict_goal(workout_type, equipment, intensity,
                                          duration_min,
                                          calories_burned)
            result = f"Input: {workout_type}, {equipment} -> Predicted Goal: {predicted_goal}"
        except Exception as e:
            result = f"Prediction Error: Model could not process request. Details: {e}"
            error_message = "Prediction failed."

    # 3. Fetch history and Render the page with the result
    run_history: List[RunLogResponse] = await service.get_user_run_history(
        current_user.id)

    return templates.TemplateResponse(
        "recommend.html",
        {"request": request,
         "error": error_message,
         "equipment_options": valid_equipment,
         "intensity_options": valid_intensity,
         "workout_type_options": valid_workout_types,
         "current_user": current_user,
         "run_history": run_history,
         "current_view": current_view,  # Keep the running tab context
         # PASS SUBMITTED VALUES BACK TO THE TEMPLATE CONTEXT:
         "workout_type": workout_type,
         "equipment": equipment,
         "intensity": intensity,
         "duration_min": duration_min,
         "calories_burned": calories_burned,
         "result": result}
    )


# --- New HTML Form Handlers for Running Hub (POST -> Redirect GET) ---

@app.post("/v1/running/logs-html", response_class=RedirectResponse)
async def log_run_from_html_form(
        db_session: AsyncSession = Depends(get_db_session),
        current_user: UserOut = Depends(get_current_user),
        service: RunningService = Depends(get_running_service),
        distance_km: float = Form(...),
        duration_min: float = Form(...),
        avg_heart_rate: int = Form(...),
        run_type: str = Form(...),
        redirect_to: str = Form("/recommend?view=log-run")
        # Target URL from the hidden field
):
    """Handles HTML form submission for logging a run and redirects back to the main page."""

    run_data = RunLogCreate(
        distance_km=distance_km,
        duration_min=duration_min,
        avg_heart_rate=avg_heart_rate,
        run_type=run_type
    )

    try:
        await service.create_run_log(current_user.id, run_data)
        # Redirect back to the form with success status. Use 303 for POST-after-redirect.
        return RedirectResponse(f"/recommend?view=log-run&log_status=success",
                                status_code=303)
    except Exception as e:
        # Redirect back with an URL-encoded error message
        error_msg = f"Failed to log run: {e}"
        return RedirectResponse(
            f"/recommend?view=log-run&running_error={quote_plus(error_msg)}",
            status_code=303)


@app.post("/v1/running/fitness-score-html", response_class=RedirectResponse)
async def predict_pace_from_html_form(
        current_user: UserOut = Depends(get_current_user),
        service: RunningService = Depends(get_running_service),
        redirect_to: str = Form("/recommend?view=predict-run")
        # Target URL from the hidden field
):
    """Handles HTML form submission for prediction and redirects back with the result."""

    try:
        # Correctly call the service method: get_running_fitness_score
        result = await service.get_running_fitness_score(current_user.id)

        # Serialize the result object to a JSON string
        result_json = json.dumps(result)

        # URL-encode the JSON string and redirect to the correct view
        return RedirectResponse(
            f"/recommend?view=predict-run&prediction_result={quote_plus(result_json)}",
            status_code=303)

    except Exception as e:
        # Redirect back with an URL-encoded error message
        error_msg = f"Failed to get prediction: {e}"
        return RedirectResponse(
            f"/recommend?view=predict-run&running_error={quote_plus(error_msg)}",
            status_code=303)