FROM alpine:3.18

# Install only basic tools, no development tools
RUN apk add --no-cache \
    bash \
    curl

# Create app directory
WORKDIR /test_files

# Keep container running
CMD ["tail", "-f", "/dev/null"]