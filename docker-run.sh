#!/bin/bash

# Docker management script for Unity Streamlit App

case "$1" in
    "build")
        echo "Building Docker image..."
        docker build -t unity-streamlit-app .
        ;;
    "run")
        echo "Running Streamlit app..."
        docker run -d -p 8501:8501 --name unity-streamlit-app unity-streamlit-app
        ;;
    "stop")
        echo "Stopping Streamlit app..."
        docker stop unity-streamlit-app
        docker rm unity-streamlit-app
        ;;
    "logs")
        echo "Showing logs..."
        docker logs -f unity-streamlit-app
        ;;
    "shell")
        echo "Opening shell in container..."
        docker exec -it unity-streamlit-app /bin/bash
        ;;
    "compose-up")
        echo "Starting with docker-compose..."
        docker-compose up -d
        ;;
    "compose-down")
        echo "Stopping with docker-compose..."
        docker-compose down
        ;;
    "compose-logs")
        echo "Showing docker-compose logs..."
        docker-compose logs -f
        ;;
    "clean")
        echo "Cleaning up Docker resources..."
        docker system prune -f
        docker image prune -f
        ;;
    *)
        echo "Usage: $0 {build|run|stop|logs|shell|compose-up|compose-down|compose-logs|clean}"
        echo ""
        echo "Commands:"
        echo "  build         - Build Docker image"
        echo "  run           - Run container manually"
        echo "  stop          - Stop and remove container"
        echo "  logs          - Show container logs"
        echo "  shell         - Open shell in container"
        echo "  compose-up    - Start with docker-compose"
        echo "  compose-down  - Stop with docker-compose"
        echo "  compose-logs  - Show docker-compose logs"
        echo "  clean         - Clean up Docker resources"
        exit 1
        ;;
esac
