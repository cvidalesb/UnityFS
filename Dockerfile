FROM python:3.11-slim

WORKDIR /app

# Install only essential system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Railway will set the PORT environment variable
ENV PORT=8501
EXPOSE $PORT

# Use Railway's start command
CMD streamlit run FeeModification_app.py --server.port=$PORT --server.address=0.0.0.0
