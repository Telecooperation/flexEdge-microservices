# Use an official Python runtime as a parent image
FROM python:3.6

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
ADD . /app

# Make port 5000 available to the world outside this container
EXPOSE 8881

# Define environment variable
#ENV NAME World

# Run app.py when the container launches
CMD ["python", "server.py"]