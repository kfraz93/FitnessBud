# FitnessBud – AI-Powered Workout Recommendation API

**Project Goal**
To build a production-grade backend API using FastAPI and Hexagonal Architecture,
featuring JWT authentication, SQLAlchemy for persistence, and a scikit-learn machine
learning component for personalized workout recommendations. This project demonstrates
full-stack backend proficiency.

Technologies Used Backend: Python, FastAPI, Uvicorn,
Backend: Python, FastAPI, Uvicorn, Pylance / MyPy

Architecture: Hexagonal Architecture (Ports and Adapters)

Database: SQLAlchemy (ORM), SQLite/PostgreSQL

Authentication: JWT (JSON Web Tokens)

Machine Learning: scikit-learn, joblib/pickle

Frontend (Phase 4): Jinja2 Templates, Bootstrap, Chart.js

DevOps: Docker, Docker Compose, GitHub Actions, Render/Railway

---

🚀 **Setup & Installation**

This project uses **uv** for fast dependency management and **Pylance/MyPy** for type checking.

1. **Clone Repository:**
   ```bash
   git clone [your_repo_url]
   cd FitnessBud
   ```

2. **Virtual Environment (using uv):**
   ```bash
   python -m venv venv
   source venv/bin/activate # or .\venv\Scripts\activate on Windows
   ```

3. **Install Dependencies (Using uv):**
   ```bash

# Use uv add for all dependencies

uv add fastapi uvicorn passlib python-jose[cryptography] sqlalchemy asyncpg pydantic-settings

# Add dependency for password hashing

uv add bcrypt

# New ML dependencies added

uv add scikit-learn pandas numpy joblib

```

4. **Run Server Verification:**
   ```bash
   uvicorn api.main:app --reload
   ```

Verify by navigating to `http://127.0.0.1:8000/docs`

---

🎯 **Phase 1 (Weeks 1–2): Project Setup & Core Architecture**

| Status | Task                                                                                  | Description                                                                                     |
|:-------|:--------------------------------------------------------------------------------------|:------------------------------------------------------------------------------------------------|
| [x]    | 1. Initialize Git repository, virtual environment, and FastAPI project.               | Already completed.                                                                              |
| [x]    | 2. Set up folder structure following Hexagonal Architecture (core, domain, adapters). | Define api/, core/, domain/, infrastructure/. Structure initialized.                            |
| [x]    | 3. Configure FastAPI, SQLAlchemy, and environment variables.                          | Create core/config.py and implement Pydantic Settings. Configuration complete.                  |
| [x]    | 4. Implement User and Workout domain models.                                          | Define SQLAlchemy ORM models and Pydantic schemas. **(Model fields finalized with timestamps)** |
| [x]    | 5. Set up database migrations (Alembic).                                              | Initialize Alembic structure and configuration.                                                 |
| [x]    | 6. Create /health endpoint and verify project runs with Uvicorn.                      | Already completed.                                                                              |

---

🔑 **Phase 2 (Weeks 3–4): Authentication & CRUD Operations**

| Status | Task                                                               | Description                                                                                                                                                                                                                                                                  |
|:-------|:-------------------------------------------------------------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [x]    | 1. Implement JWT authentication (register, login, refresh).        | Services and endpoints for secure token generation and handling. **(Completed: Registration, Login, and Token Generation are working end-to-end)**                                                                                                                           |
| [x]    | 2. Add CRUD endpoints for user workout logs.                       | Allow authenticated users to create, read, update, and delete logs. **(Completed: Secured endpoints and underlying service/repository logic)**                                                                                                                               |
| [x]    | 3. Integrate SQLAlchemy repositories and service layer logic.      | Implement the repository interfaces defined in the domain core. **(Completed)**                                                                                                                                                                                              |
| [ ]    | 4. Write unit tests with pytest for API routes and business logic. | Focus on testability enabled by Hexagonal Architecture.                                                                                                                                                                                                                      |
| [ ]    | 5. Implement GitHub Actions workflow for test automation.          | CI/CD setup for running tests on push/PR.                                                                                                                                                                                                                                    |
| [x]    | 6. FIX: Environmental/Date Serialization Bug                       | Identified critical bug where SQLite could not handle datetime.date objects with async sessions, causing a silent 500 error. FIXED by migrating to PostgreSQL via Docker Compose, eliminating all environment and connection conflicts and validating all dependency chains. |

---

🤖 **Phase 3 (Weeks 5–6): AI Model Integration (scikit-learn)**

| Status | Task                                                               | Description                                                                                                            |
|:-------|:-------------------------------------------------------------------|:-----------------------------------------------------------------------------------------------------------------------|
| [x]    | 1. Generate synthetic training data.                               | Create a simple script to generate mock data based on user profile and log data.                                       |
| [x]    | 2. Train scikit-learn model.                                       | Implement and train KMeans or DecisionTreeClassifier.                                                                  |
| [x]    | 3. Save model using joblib and load in FastAPI adapter.            | Create the infrastructure/ml_adapter.py for model loading.                                                             |
| [x]    | 4. Create /recommend endpoint that returns predicted workout plan. | Primary endpoint consuming the ML adapter.                                                                             |
| [ ]    | 5. Test AI inference with mock data.                               | Unit test the recommendation logic.                                                                                    |
| [x]    | 6. Identify Model Bias/Fixes                                       | DEBUG: Prediction error found (e.g., 'Running' for 'gain_muscle'). Requires model retraining on refined features only. |

---
🖼️ **Phase 4 (Weeks 7–8): Frontend, Deployment & Polishing**

| Status | Task                                                                       | Description                                                                                                                                 |
|:-------|:---------------------------------------------------------------------------|:--------------------------------------------------------------------------------------------------------------------------------------------|
| [ ]    | 1. Refactor ML Adapter & Architecture Cleanup                              | CRITICAL: Move ML adapter logic and prediction endpoint into correct Hexagonal layers (domain/service, infrastructure/adapter, api/router). |
| [ ]    | 2. Rework and Retrain ML Model                                             | Fix bias by retraining model on only static profile features (goal, equipment), excluding noisy log data (calories, duration).              |
| [ ]    | 3. Add Input Validation                                                    | Enforce data constraints (e.g., age >= 18, duration > 0) using Pydantic validators.                                                         |
| [x]    | 4. Add Jinja2 templates with Bootstrap for UI.                             | **Completed: Implemented basic workout input, recommendation pages, and constrained dropdown menus.**                                       |
| [ ]    | 5. Implement user dashboard with progress summary charts (Chart.js).       | Display user statistics and workout history.                                                                                                |
| [x]    | 6. Dockerize application and set up docker-compose.                        | Containerize the FastAPI app for consistent local and production deployment.                                                                |
| [ ]    | 7. Deploy on Render/Railway or similar cloud platform.                     | Set up cloud deployment pipeline.                                                                                                           |
| [ ]    | 8. Document project with README, architecture diagram, and demo video/GIF. | Final documentation and presentation assets.                                                                                                |
| [ ]    | 9. Optimize Docker Build Speed (UV Multi-Stage)                            | Implement a Docker multi-stage build using UV to dramatically reduce dependency installation time.                                          |
| [ ]    | 10. Define Running App Data Model (New Feature)                            | Define new SQLAlchemy RunLog model (Distance, Duration, HR) to enable meaningful ML.                                                        |
| [ ]    | 11. Implement Running App Core Services                                    | Create new domain/service and repository layers for the RunLog entity.                                                                      |
| [ ]    | 12. Implement Pace Prediction ML Model                                     | Retrain Scikit-learn model as a Regression model to predict optimal pace/duration.                                                          |