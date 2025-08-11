# Use a small Python base image
FROM python:3.12-alpine

# Install system dependencies for yfinance and feedgen
RUN apk add --no-cache gcc g++ libffi-dev musl-dev make

# Set working directory
WORKDIR /app

# Copy dependencies and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY main.py .

# Expose Flask port
EXPOSE 5000

# Run the application
CMD ["python", "main.py"]

