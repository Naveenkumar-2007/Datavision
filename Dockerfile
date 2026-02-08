FROM python:3.11-slim

# Pre-built frontend - no build needed (avoids OOM on HuggingFace)
# Frontend built locally and dist/ folder committed to repo
# 2026-01-04 - Fixed libgomp dependency for LightGBM

WORKDIR /app

# Install system dependencies required by ML libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy pre-built frontend (built locally, committed to repo)
COPY frontend/dist /app/static

# Copy backend source files
COPY backend/ backend/

# Create ALL storage directories with proper ownership
# SECURITY: Use 755 (rwxr-xr-x) instead of 777
# 2026-02-08 - Added exports, audit, users dirs for ML training persistenc
RUN mkdir -p /app/storage/users \
             /app/backend/storage/users \
             /app/backend/storage/automl \
             /app/backend/storage/models \
             /app/backend/storage/clustering_models \
             /app/backend/storage/graph \
             /app/backend/storage/faiss \
             /app/backend/storage/uploads \
             /app/backend/storage/exports \
             /app/backend/storage/audit \
             /app/backend/catboost_info && \
    chown -R appuser:appuser /app/storage /app/backend/storage /app/backend/catboost_info /app/static && \
    chmod -R 755 /app/storage /app/backend/storage /app/backend/catboost_info

# Set ownership of entire app directory to non-root user
RUN chown -R appuser:appuser /app

# Set Python path - backend folder contains all imports
ENV PYTHONPATH=/app/backend
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

# Switch to non-root user
USER appuser

# Set working directory to backend for correct imports
WORKDIR /app/backend

# Expose HuggingFace default port
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/api || exit 1

# Start FastAPI server from backend directory
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
