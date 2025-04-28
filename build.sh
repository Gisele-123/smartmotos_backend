#!/bin/bash
# Install build dependencies first
pip install grpcio-tools>=1.62.0
# Then install the rest
pip install -r requirements.txt