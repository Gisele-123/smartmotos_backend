#!/bin/bash
# Install build dependencies first
pip install --upgrade pip
pip install Cython==3.0.12 wheel setuptools protobuf==5.26.1

# Then install requirements with dependency resolution
pip install --no-cache-dir -r requirements.txt

# Verify installation
pip check