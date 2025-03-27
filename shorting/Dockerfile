# Use an official Python runtime as the parent image
FROM python:3.10-slim

# Set the working directory in the container to /app
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    curl \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies for Real Estate module
RUN pip install --no-cache-dir streamlit-folium folium opencv-python-headless

# Copy the application code
COPY . .

# Create directories
RUN mkdir -p outputs/videos outputs/images temp

# Make sure we have our module directories
RUN mkdir -p shortGPT/modules shortGPT/utils shortGPT/prompt_templates/realestate

# Copy the real estate prompt template if needed
COPY integration_modules/realestate_prompt_template.yaml shortGPT/prompt_templates/realestate/

# Expose the port
EXPOSE 31415

# Run the application
CMD ["python", "runShortGPT.py"]