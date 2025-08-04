# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY backend/requirements.txt .

COPY public/ ./public/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend application code into the container at /app
COPY backend/ ./backend/

# Copy the chainlit.md file
COPY chainlit.md .

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable
ENV PORT 8000
ENV HOST 0.0.0.0

# Run app.py when the container launches
# The '-w' flag is removed as it is for development (watch mode)
# Chainlit will run on the host and port specified by the environment variables
CMD ["chainlit", "run", "backend/src/app.py", "--host", "0.0.0.0", "--port", "8000"]
