# Base image from NVIDIA with CUDA and PyTorch pre-installed
FROM nvcr.io/nvidia/l4t-pytorch:r35.2.1-pth2.0-py3

# Set working directory
WORKDIR /app

# Copy the project files
COPY . /app

# Install required packages
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive

# Expose necessary ports (if any)
# EXPOSE 8080

# Command to run the main application
CMD ["python3", "src/main.py"]
