FROM golang:1.21-alpine

# Install basic tools
RUN apk add --no-cache \
    bash \
    curl \
    git

# Create app directory
WORKDIR /test_files

# Verify installations
RUN go version && gofmt -h || true

# Keep container running
CMD ["tail", "-f", "/dev/null"]