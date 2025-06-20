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
        python3.11-dev \
        python3.11-venv \
        python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Create symlinks for python and pip
RUN ln -sf /usr/bin/python3.11 /usr/bin/python \
    && ln -sf /usr/bin/python3.11 /usr/bin/python3

# Install uv (but NOT ruff)
RUN python3.11 -m pip install --no-cache-dir uv

# Copy lintair binary
COPY lintair /app/lintair
RUN chmod +x /app/lintair

# Create app directory
WORKDIR /test_files

# Verify installations (note: ruff should NOT be available)
RUN python --version && pip --version && uv --version

# Check if uvx is available (it should be part of uv)
RUN which uvx || echo "uvx not in PATH, checking uv"

# Verify ruff is NOT installed
RUN ! which ruff

# Keep container running
CMD ["tail", "-f", "/dev/null"]