#!/bin/bash

# Start script for Hugging Face Spaces
# Serves both the FastAPI backend and React frontend

echo "Starting AI Business Analyst..."

# Start FastAPI backend (serves frontend static files too)
cd /app/backend

# Use uvicorn to serve the application
exec uvicorn main:app --host 0.0.0.0 --port 7860
