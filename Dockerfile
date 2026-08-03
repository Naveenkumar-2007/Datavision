FROM python:3.12-slim

# DataVision AI — Production Container
# Pre-built frontend committed as static/ — no Node.js build needed.

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

# Copy frontend public assets and pre-built dist
COPY frontend/public /app/frontend/public
COPY frontend/dist /app/static
COPY frontend/dist /app/backend/static

# Copy backend source files (includes both legacy and new app/)
COPY backend/ backend/

# Copy start script
COPY start.sh /app/
RUN chmod +x /app/start.sh

# Create storage directories with proper ownership
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

# Python path includes both backend/ (legacy) and backend/ for app.* imports
ENV PYTHONPATH=/app/backend
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV MPLCONFIGDIR=/tmp/matplotlib
ENV HOME=/tmp

# Switch to non-root user
USER appuser

# Set working directory to backend for correct imports
WORKDIR /app/backend

# Expose port
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Start using the start script (handles migrations)
CMD ["/app/start.sh"]

