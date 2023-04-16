# Base image
FROM python:3.8.2-slim-buster

# Install Rust compiler
RUN apt-get update && \
    apt-get install -y curl && \
    curl https://sh.rustup.rs -sSf | sh -s -- -y && \
    . $HOME/.cargo/env && \
    rustc --version && \
    cargo --version && \
    # apt-get remove -y curl && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# Install Git
RUN apt-get update && \
    apt-get install -y git && \
    rm -rf /var/lib/apt/lists/*

# Install psutil and dependencies for OpenCV
RUN apt-get update && \
    apt-get install -y gcc python3-dev libgl1-mesa-glx libglib2.0-0 && \
    pip install psutil && \
    apt-get remove -y gcc python3-dev && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# Install OpenCV
RUN apt-get update && apt-get install -y libgomp1

# Copy application files to container
COPY . /app

# Set working directory
WORKDIR /app

# Install required Python packages
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose port
EXPOSE 8000

# Run the application using gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app", "--timeout", "180"]
