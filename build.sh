#!/usr/bin/env bash
# Render build script — installs system deps needed for scipy then pip install
set -o errexit

# Install system dependencies for scipy compilation
apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ gfortran libopenblas-dev pkg-config \
  && rm -rf /var/lib/apt/lists/*

pip install --upgrade pip
pip install -r requirements.txt
