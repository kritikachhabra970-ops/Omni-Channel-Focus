# Use a stable, official Python slim image as base
FROM python:3.11-slim

# Set environment variables to optimize Python performance inside the container
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=10000

# Set working directory inside the container
WORKDIR /app

# Copy requirements file first to take advantage of Docker build caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . .

# Expose the port
EXPOSE 10000

# Start the application using gunicorn and eventlet worker
CMD ["sh", "-c", "gunicorn --worker-class eventlet -w 1 -b 0.0.0.0:$PORT app:app"]


 