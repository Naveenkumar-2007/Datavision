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

# Create storage directories with proper ownership
# SECURITY: Use 755 (rwxr-xr-x) instead of 777
RUN mkdir -p /app/storage /app/backend/storage && \
    chown -R appuser:appuser /app/storage /app/backend/storage /app/static && \
    chmod -R 755 /app/storage /app/backend/storage

# Set ownership of entire app directory to non-root user
RUN chown -R appuser:appuser /app

# Set Python path
ENV PYTHONPATH=/app/backend:/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Switch to non-root user
USER appuser

# Expose HuggingFace default port
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/api || exit 1

# Start FastAPI server
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
