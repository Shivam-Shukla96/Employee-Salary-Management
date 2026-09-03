FROM python:3.12-slim

WORKDIR /app

# Ensure Python output is sent straight to terminal and /app is in PYTHONPATH
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Install system dependencies for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies from backend directory
COPY backend/pyproject.toml ./pyproject.toml
RUN pip install --no-cache-dir .

# Copy application code from backend directory
COPY backend/ /app/
RUN pip install --no-cache-dir -e .

EXPOSE 8000

# Run migrations and start uvicorn production server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
