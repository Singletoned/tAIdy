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

# Install black (but NOT ruff or uv)
RUN python3.11 -m pip install --no-cache-dir black

# Copy lintair binary
COPY lintair /app/lintair
RUN chmod +x /app/lintair

# Create app directory
WORKDIR /test_files

# Verify installations
RUN python --version && pip --version && black --version

# Verify ruff and uv are NOT installed
RUN ! which ruff
RUN ! which uv

# Keep container running
CMD ["tail", "-f", "/dev/null"]