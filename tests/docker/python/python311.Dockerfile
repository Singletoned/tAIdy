FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install basic tools and Python 3.11
RUN apt-get update && apt-get install -y \
    bash \
    curl \
    git \
    ca-certificates \
    software-properties-common \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python 3.11
RUN add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get install -y \
        python3.11 \
        python3.11-pip \
        python3.11-dev \
        python3.11-venv \
    && rm -rf /var/lib/apt/lists/*

# Create symlinks for python and pip
RUN ln -sf /usr/bin/python3.11 /usr/bin/python \
    && ln -sf /usr/bin/python3.11 /usr/bin/python3

# Install ruff
RUN python3.11 -m pip install --no-cache-dir ruff==0.1.6

# Create app directory
WORKDIR /test_files

# Verify installations
RUN python --version && pip --version && ruff --version

# Keep container running
CMD ["tail", "-f", "/dev/null"]