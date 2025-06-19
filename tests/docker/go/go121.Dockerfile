FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install basic tools
RUN apt-get update && apt-get install -y \
    bash \
    curl \
    git \
    ca-certificates \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Go 1.21
RUN wget -O go1.21.linux-amd64.tar.gz https://go.dev/dl/go1.21.5.linux-amd64.tar.gz \
    && tar -C /usr/local -xzf go1.21.linux-amd64.tar.gz \
    && rm go1.21.linux-amd64.tar.gz

# Set Go environment variables
ENV PATH=/usr/local/go/bin:$PATH
ENV GOPATH=/go
ENV GOROOT=/usr/local/go

# Copy lintair binary
COPY lintair /app/lintair
RUN chmod +x /app/lintair

# Create app directory
WORKDIR /test_files

# Verify installations
RUN go version && gofmt -h || true

# Keep container running
CMD ["tail", "-f", "/dev/null"]