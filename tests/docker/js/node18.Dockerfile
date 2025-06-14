FROM node:18-alpine

# Install basic tools
RUN apk add --no-cache \
    bash \
    curl \
    git

# Install prettier globally
RUN npm install -g prettier@^3.0.0

# Create app directory
WORKDIR /test_files

# Verify installations
RUN node --version && npm --version && prettier --version

# Keep container running
CMD ["tail", "-f", "/dev/null"]