# 🏋️ FitnessBud – AI-Powered Backend Recommendation API

FitnessBud is a production-grade backend application built with **FastAPI** and **Hexagonal Architecture** (Ports and Adapters). It features secure JWT authentication, PostgreSQL persistence via SQLAlchemy, and an integrated machine learning component. The project is fully containerized using Docker for consistent, repeatable deployment.

## 🚀 Key Architectural & Technical Features

* **Hexagonal Architecture:** Strict separation of concerns using **Domain**, **Service**, and **Infrastructure/Adapter** layers, ensuring high testability and maintainability.
* **API Framework:** **FastAPI** for high performance and automatic interactive documentation (`/docs`).
* **Database:** **PostgreSQL** persistence managed via **SQLAlchemy ORM** and **Alembic** migrations.
* **Authentication:** Secure **JWT (JSON Web Tokens)** implementation for user registration, login, and protected routes.
* **Containerization:** Full setup using **Docker** and **Docker Compose** for local development and deployment consistency.
* **Machine Learning Integration:** A Scikit-learn model, persisted via **Joblib**, is loaded into a dedicated API endpoint for workout recommendations.
* **Frontend PoC:** Integrated **Jinja2** templates provide a basic demonstration of the API's consumer layer.

## ⚙️ Setup and Running Locally (Docker Compose)

The easiest way to run the entire stack (FastAPI app and PostgreSQL database) is using Docker Compose.

1.  **Clone the repository:**
    ```bash
    git clone [Your Repo URL]
    cd FitnessBud
    ```

2.  **Build and run the containers:**
    ```bash
    docker compose up --build
    ```

3.  **Access the Application:**
    * **Frontend (PoC):** `http://localhost:8000/`
    * **Interactive API Docs (Swagger UI):** `http://localhost:8000/docs`

## 🧠 Future Development: Shifting Focus

The current ML model for the Gym domain is highly constrained due to data complexity. Future development will introduce a parallel **Running Log feature** with a new **Regression ML model** to deliver meaningful, actionable predictions (e.g., predicting optimal pace or duration) for a simplified domain, enhancing the core value of the API.