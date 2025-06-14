FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install only basic tools, no development tools
RUN apt-get update && apt-get install -y \
    bash \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /test_files

# Keep container running
CMD ["tail", "-f", "/dev/null"]