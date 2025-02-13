# Use a Linux base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy files to container
COPY . /app

# Set working directory to /app
WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose necessary ports
EXPOSE 5000 5001 5002 5003 5004 5005 5007

# Run the application
CMD ["python", "runbatch.py"]