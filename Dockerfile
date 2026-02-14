# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Install poetry
RUN pip install --no-cache-dir poetry==2.2.1

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Export dependencies to requirements.txt
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from builder
COPY --from=builder /app/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY inquisitool/ ./inquisitool/

# Create upload directory
RUN mkdir -p upload

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "inquisitool.main", "run", "--host", "0.0.0.0", "--port", "8000"]
