FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml .

# Install Python dependencies
RUN pip install --no-cache-dir .

# Copy application code
COPY inquisitool/ ./inquisitool/

# Create upload directory
RUN mkdir -p upload

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "inquisitool.main", "run", "--host", "0.0.0.0", "--port", "8000"]
