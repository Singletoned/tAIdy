FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install basic tools and Node.js
RUN apt-get update && apt-get install -y \
    bash \
    curl \
    git \
    ca-certificates \
    gnupg \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 18 from NodeSource repository
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Install prettier globally
RUN npm install -g prettier@^3.0.0

# Create app directory
WORKDIR /test_files

# Verify installations
RUN node --version && npm --version && prettier --version

# Keep container running
CMD ["tail", "-f", "/dev/null"]