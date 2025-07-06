# Stage 1: Build dependencies
FROM python:3.9-slim-buster as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Stage 2: Final image
FROM python:3.9-slim-buster

WORKDIR /app

# Copy cached wheels from builder stage
COPY --from=builder /app/wheels /wheels
COPY --from=builder /usr/local/bin/gunicorn /usr/local/bin/gunicorn # Copy gunicorn executable
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels

COPY app/ /app/app/

# Expose the port Gunicorn will run on
EXPOSE 5000

# Command to run the application using Gunicorn
CMD ["python", "app/main.py"]