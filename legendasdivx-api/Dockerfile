FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY app/ app/

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Create data directories
RUN mkdir -p /data /logs

# Expose port
EXPOSE 8000

# Run app with uvicorn
# Cloud Run sets PORT env variable, default to 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
