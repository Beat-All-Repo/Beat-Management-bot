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

# Install setuptools first to ensure pkg_resources is always available,
# then install remaining dependencies
RUN pip3 install --root-user-action=ignore -U pip && \
    pip3 install --root-user-action=ignore -U setuptools wheel && \
    pip3 install --root-user-action=ignore -U -r requirements.txt

# Copy rest of the project
COPY . .

# Expose port for Render keep-alive health check
EXPOSE 8080

# Run the bot
CMD ["python3", "-m", "FallenRobot"]
