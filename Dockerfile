FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update -y && \
    apt-get upgrade -y && \
    apt-get install -y \
    git \
    ffmpeg \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install -U pip setuptools wheel --root-user-action=ignore && \
    pip3 install -U -r requirements.txt --root-user-action=ignore

# Copy rest of the project
COPY . .

# Expose port for Render keep-alive health check
EXPOSE 8080

# Run the bot
CMD ["python3", "-m", "FallenRobot"]
