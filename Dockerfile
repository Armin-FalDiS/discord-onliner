# Use Alpine Linux with Python for a lightweight image
FROM python:3.9-alpine

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the script
COPY discord.py .

# Run the script with unbuffered output for immediate logging
CMD ["python", "-u", "discord.py"]
