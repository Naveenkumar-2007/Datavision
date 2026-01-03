FROM python:3.11-slim

# Force rebuild with updated requirements - 2025-12-12-v2
WORKDIR /app

# Install Node.js for frontend build
RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy and build frontend
COPY frontend/package*.json frontend/
WORKDIR /app/frontend
RUN npm ci
COPY frontend/ .
RUN npm run build

# Copy ALL backend source files
WORKDIR /app
COPY backend/ backend/

# Create directory for serving frontend
RUN mkdir -p /app/static && cp -r /app/frontend/dist/* /app/static/

# Set Python path to include backend directory
ENV PYTHONPATH=/app/backend:/app

# Expose HuggingFace default port
EXPOSE 7860

# Start FastAPI server (running from /app, so use backend.main)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
