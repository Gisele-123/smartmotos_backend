#!/bin/bash
# Install build dependencies first
pip install --upgrade pip
pip install Cython==3.0.12 wheel setuptools
# Then install requirements
pip install -r requirements.txt