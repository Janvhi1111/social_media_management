# Use the official Python image from the Docker Hub
FROM python:3.12-slim

# Set a working directory inside the container
WORKDIR /app

# Copy the current directory (your Python app) to /app in the container
COPY . /app

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port that Streamlit runs on (default is 8501)
EXPOSE 8501

# Command to run the app when the container starts
CMD ["streamlit", "run", "social_media_managment.py", "--server.port=8501", "--server.headless=true"]