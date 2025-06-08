FROM python:3.9-slim

WORKDIR /app

# Copy static files
COPY . .

# Expose port 8000
EXPOSE 8000

# Start Python HTTP server
CMD ["python3", "-m", "http.server", "8000"] 