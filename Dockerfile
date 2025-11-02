# Use the official Python 3.12 slim image
FROM python:3.12-slim

# Set environment variables for non-buffered output
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory inside the container
WORKDIR /app

# Copy dependency file first
COPY pyproject.toml .

# Install dependencies listed in pyproject.toml directly using pip.
# The '.[project]' syntax tells pip to install the package and its defined dependencies.
# We also install the pandas-stubs package which pip might fail to resolve correctly otherwise.
RUN pip install --no-cache-dir .

# Copy the rest of the application code
COPY . /app/

# Expose the port Uvicorn runs on
EXPOSE 8000

# Command to run the application using uvicorn
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]