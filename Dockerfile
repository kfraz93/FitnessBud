FROM python:3.12-slim

# Turn off Python buffering for better logging
ENV PYTHONUNBUFFERED=1

WORKDIR /code

# Install uv package manager
RUN pip install --no-cache-dir uv

# Copy pyproject.toml (allows uv to install correct deps before code)
COPY pyproject.toml /code/

# COPY .env /code/.env

# Install dependencies into system Python
RUN uv pip install --system .

# Copy actual source code
COPY api /code/api
# COPY application /code/application
COPY core /code/core
COPY domain /code/domain
COPY infrastructure /code/infrastructure
COPY static /code/static
COPY templates /code/templates
COPY models /code/models

# Expose the FastAPI port
EXPOSE 80

# Run server
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "80"]