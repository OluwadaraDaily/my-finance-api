#!/usr/bin/env bash
# exit on error
set -o errexit

# Install system dependencies for mysqlclient
apt-get update
apt-get install -y python3-dev default-libmysqlclient-dev build-essential pkg-config

# Install Python dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head