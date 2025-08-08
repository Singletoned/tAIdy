# Multi-stage Taidy Docker Image - Optimized for fast startup time
# Stage 1: Builder - Install and compile all tools
FROM alpine:3.19 AS builder

# Install build dependencies and system tools in a single layer
RUN apk add --no-cache \
    # Basic system tools
    bash \
    curl \
    wget \
    git \
    unzip \
    build-base \
    ca-certificates \
    # Python build dependencies
    python3 \
    python3-dev \
    py3-pip \
    # Node.js
    nodejs \
    npm \
    # Ruby build dependencies
    ruby \
    ruby-dev \
    ruby-bundler \
    # PHP and related tools
    php82 \
    php82-cli \
    php82-mbstring \
    php82-xml \
    php82-phar \
    php82-openssl \
    php82-curl \
    # System linters available in Alpine
    shellcheck \
    # Go (will install from binary)
    # Rust (will install via rustup)
    && ln -sf /usr/bin/python3 /usr/bin/python

# Install Go from official binary
RUN GOARCH=$(case $(uname -m) in x86_64) echo amd64;; aarch64) echo arm64;; *) uname -m;; esac) && \
    wget -O go.tar.gz "https://go.dev/dl/go1.21.5.linux-${GOARCH}.tar.gz" && \
    tar -C /usr/local -xzf go.tar.gz && \
    rm go.tar.gz
ENV PATH=/usr/local/go/bin:$PATH

# Install Rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
ENV PATH=/root/.cargo/bin:$PATH

# Install Composer for PHP
RUN curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer

# Install Python tools (combining pip installs for efficiency)
RUN pip3 install --no-cache-dir --target=/opt/python-tools \
    ruff \
    black \
    flake8 \
    pylint \
    yamllint \
    beautysh

# Install Node.js tools globally
RUN npm install -g \
    eslint \
    prettier \
    typescript

# Install Go tools
ENV GOBIN=/opt/go-tools
RUN mkdir -p $GOBIN && \
    go install mvdan.cc/sh/v3/cmd/shfmt@latest

# Install binary releases for tools that are problematic to compile
RUN mkdir -p /opt/bin && \
    ARCH=$(case $(uname -m) in x86_64) echo amd64;; aarch64) echo arm64;; *) echo amd64;; esac) && \
    # Install actionlint (with error handling for missing ARM64 builds)
    (curl -L -o actionlint.tar.gz "https://github.com/rhymond/actionlint/releases/download/v1.6.26/actionlint_1.6.26_linux_${ARCH}.tar.gz" && \
     tar -xzf actionlint.tar.gz -C /opt/bin && rm actionlint.tar.gz) || \
    (echo "Warning: actionlint not available for ${ARCH}, skipping") && \
    # Install trufflehog (with error handling)
    (curl -sSfL "https://github.com/trufflesecurity/trufflehog/releases/download/v3.63.7/trufflehog_3.63.7_linux_${ARCH}.tar.gz" | \
     tar -xz -C /opt/bin trufflehog) || \
    (echo "Warning: trufflehog not available for ${ARCH}, skipping") && \
    # Install Terraform
    curl -L -o terraform.zip "https://releases.hashicorp.com/terraform/1.6.6/terraform_1.6.6_linux_${ARCH}.zip" && \
    unzip terraform.zip -d /opt/bin && \
    rm terraform.zip && \
    # Install tflint (with error handling)
    (curl -L -o tflint.zip "https://github.com/terraform-linters/tflint/releases/download/v0.49.0/tflint_linux_${ARCH}.zip" && \
     unzip tflint.zip -d /opt/bin && rm tflint.zip) || \
    (echo "Warning: tflint not available for ${ARCH}, skipping") && \
    # Ensure binaries are executable
    find /opt/bin -type f -exec chmod +x {} + 2>/dev/null || true

# Install Rust tools (to /root/.cargo/bin)
RUN cargo install taplo-cli --locked && \
    cargo install just --locked

# Install Ruby tools
RUN gem install rubocop --no-document

# Install PHP tools via Composer
RUN composer global require friendsofphp/php-cs-fixer --no-dev --optimize-autoloader

# Copy and install Taidy
WORKDIR /app
COPY taidy/ /app/taidy/
COPY pyproject.toml /app/
COPY README.md /app/
RUN pip3 install --target=/opt/python-tools .

# Stage 2: Runtime - Minimal image with only necessary files
FROM alpine:3.19

# Install minimal runtime dependencies
RUN apk add --no-cache \
    bash \
    python3 \
    nodejs \
    ruby \
    php82 \
    php82-cli \
    php82-mbstring \
    php82-xml \
    php82-phar \
    php82-openssl \
    shellcheck \
    git \
    ca-certificates \
    && ln -sf /usr/bin/python3 /usr/bin/python

# Copy Go runtime (just the essentials)
COPY --from=builder /usr/local/go/bin/go /usr/local/bin/
COPY --from=builder /usr/local/go/bin/gofmt /usr/local/bin/

# Copy Rust runtime
COPY --from=builder /root/.cargo/bin/rustfmt /usr/local/bin/
COPY --from=builder /root/.cargo/bin/taplo /usr/local/bin/
COPY --from=builder /root/.cargo/bin/just /usr/local/bin/

# Copy Go tools from builder
COPY --from=builder /opt/go-tools/shfmt /usr/local/bin/

# Copy binary tools from builder (with error handling for missing files)
COPY --from=builder /opt/bin/ /usr/local/bin/

# Copy Python tools and Taidy installation
COPY --from=builder /opt/python-tools /usr/local/lib/python3.11/site-packages/
ENV PYTHONPATH=/usr/local/lib/python3.11/site-packages

# Copy Node.js global packages (npm global directory)
COPY --from=builder /usr/local/lib/node_modules /usr/local/lib/node_modules
COPY --from=builder /usr/local/bin/eslint /usr/local/bin/
COPY --from=builder /usr/local/bin/prettier /usr/local/bin/
COPY --from=builder /usr/local/bin/tsc /usr/local/bin/

# Copy Ruby gems (RubyGems install directory)
COPY --from=builder /usr/local/bundle /usr/local/bundle
COPY --from=builder /usr/local/bin/rubocop /usr/local/bin/

# Copy PHP Composer tools
COPY --from=builder /root/.composer /root/.composer

# Set up PATH environment variables for all tools
ENV PATH="/usr/local/bin:/root/.composer/vendor/bin:$PATH" \
    PYTHONPATH="/usr/local/lib/python3.11/site-packages" \
    GEM_PATH="/usr/local/bundle" \
    BUNDLE_PATH="/usr/local/bundle"

# Create optimized health check script (using sh instead of bash for speed)
RUN printf '#!/bin/sh\necho "=== Tool Health Check ==="\npython3 -m taidy suggest 2>/dev/null || echo "Taidy installed successfully"\necho "Available tools:"\npython3 --version && echo "✓ Python"\nruff --version 2>/dev/null && echo "✓ ruff" || echo "✗ ruff"\nblack --version 2>/dev/null && echo "✓ black" || echo "✗ black"\neslint --version 2>/dev/null && echo "✓ eslint" || echo "✗ eslint"\nprettier --version 2>/dev/null && echo "✓ prettier" || echo "✗ prettier"\ntsc --version 2>/dev/null && echo "✓ tsc" || echo "✗ tsc"\ngofmt -h >/dev/null 2>&1 && echo "✓ gofmt" || echo "✗ gofmt"\nshfmt --version 2>/dev/null && echo "✓ shfmt" || echo "✗ shfmt"\nactionlint --version 2>/dev/null && echo "✓ actionlint" || echo "✗ actionlint"\ntrufflehog --version 2>/dev/null && echo "✓ trufflehog" || echo "✗ trufflehog"\nrustfmt --version 2>/dev/null && echo "✓ rustfmt" || echo "✗ rustfmt"\ntaplo --version 2>/dev/null && echo "✓ taplo" || echo "✗ taplo"\njust --version 2>/dev/null && echo "✓ just" || echo "✗ just"\nrubocop --version 2>/dev/null && echo "✓ rubocop" || echo "✗ rubocop"\nphp-cs-fixer --version 2>/dev/null && echo "✓ php-cs-fixer" || echo "✗ php-cs-fixer"\nshellcheck --version 2>/dev/null && echo "✓ shellcheck" || echo "✗ shellcheck"\nyamllint --version 2>/dev/null && echo "✓ yamllint" || echo "✗ yamllint"\nbeautysh --version 2>/dev/null && echo "✓ beautysh" || echo "✗ beautysh"\nterraform --version 2>/dev/null && echo "✓ terraform" || echo "✗ terraform"\ntflint --version 2>/dev/null && echo "✓ tflint" || echo "✗ tflint"\n' > /usr/local/bin/healthcheck && chmod +x /usr/local/bin/healthcheck

# Create lightweight entrypoint script
RUN printf '#!/bin/sh\ncd /workspace 2>/dev/null || true\nexec python3 -m taidy "$@"\n' > /usr/local/bin/entrypoint.sh && \
    chmod +x /usr/local/bin/entrypoint.sh

# Set working directory
WORKDIR /workspace

# Set the entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# Default command shows help
CMD ["--help"]
