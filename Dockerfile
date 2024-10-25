# Use an official Python runtime as the base image
FROM python:3.9-slim

# Install cron
RUN apt-get update && apt-get -y install cron

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy your Python script and start.sh
COPY perilipsi.py ./
COPY start.sh ./

# Make start.sh executable
RUN chmod +x ./start.sh

# Create the log file to be able to run tail
RUN touch /var/log/cron.log

# Set the entrypoint to your start.sh script
ENTRYPOINT ["./start.sh"]
