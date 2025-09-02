#!/bin/bash

echo "Cleaning Docker build cache and rebuilding..."

# Remove any existing containers
docker-compose down 2>/dev/null || true
docker stop unity-streamlit-app 2>/dev/null || true
docker rm unity-streamlit-app 2>/dev/null || true

# Remove the image
docker rmi unity-streamlit-app 2>/dev/null || true

# Clean build cache
docker builder prune -f

# Build fresh image
echo "Building fresh Docker image..."
docker build --no-cache -t unity-streamlit-app .

echo "Build complete! You can now run:"
echo "  docker run -d -p 8501:8501 --name unity-streamlit-app unity-streamlit-app"
echo "  or"
echo "  docker-compose up -d"
