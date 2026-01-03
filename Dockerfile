FROM python:3.11-slim

# Pre-built frontend - no build needed (avoids OOM on HuggingFace)
# Frontend built locally and dist/ folder committed to repo
# 2026-01-04 - Fixed libgomp dependency for LightGBM

WORKDIR /app

# Install system dependencies required by ML libraries
RUN apt-get update && apt-get install -y \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy pre-built frontend (built locally, committed to repo)
COPY frontend/dist /app/static

# Copy backend source files
COPY backend/ backend/

# Set Python path
ENV PYTHONPATH=/app/backend:/app

# Expose HuggingFace default port
EXPOSE 7860

# Start FastAPI server
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
