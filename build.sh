#!/bin/bash
# Install build dependencies first
pip install --upgrade pip
pip install setuptools wheel
pip install grpcio-tools==1.71.0
# Then install the rest
pip install -r requirements.txt