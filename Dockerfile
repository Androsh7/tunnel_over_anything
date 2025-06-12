# Load the python image from docker
FROM docker.io/library/python:3.11-slim@sha256:7a3ed1226224bcc1fe5443262363d42f48cf832a540c1836ba8ccbeaadf8637c

# Set the working directory in the container
WORKDIR /tunnel_over_anything

# Copy the current directory contents into the container at /tunnel_over_anything
COPY . /tunnel_over_anything

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Run the application
ENTRYPOINT ["python", "main.py"]