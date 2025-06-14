FROM python:3.11-alpine

# Install basic tools
RUN apk add --no-cache \
    bash \
    curl \
    git \
    gcc \
    musl-dev

# Install ruff
RUN pip install --no-cache-dir ruff==0.1.6

# Create app directory
WORKDIR /test_files

# Verify installations
RUN python --version && pip --version && ruff --version

# Keep container running
CMD ["tail", "-f", "/dev/null"]