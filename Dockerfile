FROM python:3.11-slim

# Force rebuild with optimized build order - 2026-01-03
WORKDIR /app

# Install Node.js for frontend build FIRST (before heavy Python deps)
RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Build frontend FIRST (before Python deps to avoid OOM)
COPY frontend/package*.json frontend/
WORKDIR /app/frontend
RUN npm ci

# Copy frontend source and build with memory limit
COPY frontend/ .
ENV NODE_OPTIONS="--max-old-space-size=2048"
RUN npm run build

# Now install Python dependencies (after frontend build is done)
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy ALL backend source files
COPY backend/ backend/

# Create directory for serving frontend
RUN mkdir -p /app/static && cp -r /app/frontend/dist/* /app/static/

# Set Python path to include backend directory
ENV PYTHONPATH=/app/backend:/app

# Expose HuggingFace default port
EXPOSE 7860

# Start FastAPI server (running from /app, so use backend.main)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
