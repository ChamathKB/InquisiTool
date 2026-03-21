# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY pyproject.toml README.md ./
COPY inquisitool/ ./inquisitool/

RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir .

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app/inquisitool ./inquisitool

ENV PATH="/opt/venv/bin:$PATH"

RUN mkdir -p upload

EXPOSE 8000

CMD ["python", "-m", "inquisitool.main", "run", "--host", "0.0.0.0", "--port", "8000"]
