FROM mcr.microsoft.com/devcontainers/python:3.11

# Install Tectonic (Rust-based LaTeX engine, ~50MB vs ~500MB for texlive).
# The drop-sh installer unpacks the `tectonic` binary into the current directory,
# so run it in a known dir and move the binary onto PATH from there.
RUN cd /tmp \
    && curl --proto '=https' --tlsv1.2 -fsSL https://drop-sh.fullyjustified.net | sh \
    && mv /tmp/tectonic /usr/local/bin/tectonic \
    && chmod +x /usr/local/bin/tectonic

# Install uv (fast Python package manager). UV_INSTALL_DIR puts the binaries
# straight onto PATH so we don't have to guess the installer's default location.
RUN curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin sh

# Manim and multimedia dependencies (optional, for fsb-video template)
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
        ffmpeg \
        libcairo2-dev \
        libpango1.0-dev \
        pkg-config \
        build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
