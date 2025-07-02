# Taidy Docker Image - All formatters and linters included
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    unzip \
    gnupg \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python and pip
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js and npm
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Install Go
RUN wget https://go.dev/dl/go1.21.5.linux-amd64.tar.gz \
    && tar -C /usr/local -xzf go1.21.5.linux-amd64.tar.gz \
    && rm go1.21.5.linux-amd64.tar.gz
ENV PATH=/usr/local/go/bin:$PATH

# Install Rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH=/root/.cargo/bin:$PATH

# Install Ruby and RubyGems
RUN apt-get update && apt-get install -y \
    ruby \
    ruby-dev \
    && rm -rf /var/lib/apt/lists/*

# Install PHP and Composer
RUN apt-get update && apt-get install -y \
    php \
    php-cli \
    php-mbstring \
    php-xml \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer

# Install system tools
RUN apt-get update && apt-get install -y \
    shellcheck \
    && rm -rf /var/lib/apt/lists/*

# Install Python tools
RUN pip3 install --no-cache-dir \
    ruff \
    black \
    flake8 \
    pylint \
    yamllint

# Install Node.js tools
RUN npm install -g \
    eslint \
    prettier \
    typescript

# Install Go tools
RUN go install mvdan.cc/sh/v3/cmd/shfmt@latest

# Install Rust tools (rustfmt comes with Rust by default)
# rustfmt is already available

# Install Ruby tools
RUN gem install rubocop

# Install PHP tools
RUN composer global require friendsofphp/php-cs-fixer
ENV PATH=/root/.composer/vendor/bin:$PATH

# Install additional shell formatting tools
RUN pip3 install --no-cache-dir beautysh

# Install TOML tools
RUN cargo install taplo-cli

# Install Terraform
RUN wget https://releases.hashicorp.com/terraform/1.6.6/terraform_1.6.6_linux_amd64.zip \
    && unzip terraform_1.6.6_linux_amd64.zip \
    && mv terraform /usr/local/bin/ \
    && rm terraform_1.6.6_linux_amd64.zip

# Install tflint
RUN curl -s https://raw.githubusercontent.com/terraform-linters/tflint/master/install_linux.sh | bash

# Install hadolint (Docker linter)
RUN wget https://github.com/hadolint/hadolint/releases/download/v2.12.0/hadolint-Linux-x86_64 \
    && chmod +x hadolint-Linux-x86_64 \
    && mv hadolint-Linux-x86_64 /usr/local/bin/hadolint

# Set up working directory
WORKDIR /app

# Copy Taidy source code
COPY taidy/ /app/taidy/
COPY pyproject.toml /app/
COPY README.md /app/

# Install Taidy
RUN pip3 install .

# Create entrypoint script
RUN echo '#!/bin/bash\n\
# Change to the mounted directory\n\
cd /workspace\n\
# Run taidy with all arguments\n\
exec python3 -m taidy "$@"' > /entrypoint.sh \
    && chmod +x /entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Default command shows help
CMD ["--help"]
