# Use an official Python runtime as the base image
FROM python:3.9-slim

# Install cron
RUN apt-get update && apt-get -y install cron

# Set the working directory and copy the Python script
WORKDIR /app
COPY perilipsi.py ./
COPY .env ./

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt


# Create the log file to be able to run tail
RUN touch /var/log/cron.log

# Setup cron job (run every minute for testing)
RUN (crontab -l ; echo "0 0 * * * /usr/local/bin/python /app/perilipsi.py >> /var/log/cron.log 2>&1") | crontab

# Run the command on container startup
CMD cron && tail -f /var/log/cron.log
