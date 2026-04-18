# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (including ffmpeg for video processing)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Create downloads directory and ensure it has proper permissions
RUN mkdir -p downloads && chmod 777 downloads

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "web_app.main:app", "--host", "0.0.0.0", "--port", "8000"]
