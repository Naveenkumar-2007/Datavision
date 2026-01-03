# ==========================================
# Stage 1: Build Frontend
# ==========================================
FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend

# Copy package files and install dependencies
COPY frontend/package*.json ./
RUN npm ci --legacy-peer-deps

# Copy frontend source and build
COPY frontend/ .

# Build with increased memory limit
ENV NODE_OPTIONS="--max-old-space-size=4096"
RUN npm run build

# ==========================================
# Stage 2: Production Runtime
# ==========================================
FROM python:3.11-slim

# Force rebuild - 2026-01-03-v3-multistage
WORKDIR /app

# Install Python dependencies first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy built frontend from builder stage
COPY --from=frontend-builder /app/frontend/dist /app/static

# Copy backend source files
COPY backend/ backend/

# Set Python path
ENV PYTHONPATH=/app/backend:/app

# Expose HuggingFace default port
EXPOSE 7860

# Start FastAPI server
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
