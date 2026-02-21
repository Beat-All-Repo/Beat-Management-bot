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

# Install setuptools first, then all requirements,
# then force-reinstall setuptools so nothing can remove it
RUN pip3 install --root-user-action=ignore -U pip && \
    pip3 install --root-user-action=ignore -U setuptools wheel && \
    pip3 install --root-user-action=ignore -U -r requirements.txt && \
    pip3 install --root-user-action=ignore --force-reinstall "setuptools>=65.0.0"

# Copy rest of the project
COPY . .

# Expose port for Render keep-alive health check
EXPOSE 8080

# Run the bot
CMD ["python3", "-m", "FallenRobot"]
