FROM debian:13.0-slim

# Get a nice shell, python 3.13, and basics
RUN apt-get update && apt-get install -y \
    fish \
    python3 \
    curl \
    nodejs \
    git \
    libatomic1


# Get uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
# Get taskfile
RUN sh -c "$(curl --location https://taskfile.dev/install.sh)" -- -d -b /usr/local/bin
# Get pnpm
ENV SHELL=/bin/bash
RUN curl -fsSL https://get.pnpm.io/install.sh | sh -

CMD ["sleep", "infinity"]
