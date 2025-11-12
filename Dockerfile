# Build stage
FROM python:3.13-slim AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy only the files needed for installing dependencies
COPY pyproject.toml ./

# Install project dependencies and uvicorn
RUN pip install --user --no-warn-script-location -e . && \
    pip install --user uvicorn

# Runtime stage
FROM python:3.13-slim AS runtime

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app"

# Set working directory
WORKDIR /app

# Create a non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser \
    && chown -R appuser:appuser /app
USER appuser

# Expose the port the app runs on
EXPOSE 8000

# Copy only the necessary files from builder
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local
COPY --from=builder /app/ /app/
COPY ./src /app/src


# Command to run the application
# python -m uvicorn src.practice02.main:real_app --host 0.0.0.0 --port 8000
CMD ["python", "-m", "uvicorn", "src.practice02.main:real_app", "--host", "0.0.0.0", "--port", "8000"]
