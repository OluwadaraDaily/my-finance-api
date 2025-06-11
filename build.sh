#!/usr/bin/env bash
# exit on error
set -o errexit

echo "🚀 Starting build process..."

# Update apt with verbose logging
echo "📦 Updating apt packages..."
apt-get clean
apt-get update -y

echo "📦 Installing system dependencies..."
apt-get install -y python3-dev default-libmysqlclient-dev build-essential pkg-config

echo "🐍 Installing Python dependencies..."
pip install -r requirements.txt
pip install mysqlclient mysql-connector-python

echo "🔄 Running database migrations..."
alembic upgrade head

echo "✅ Build process completed!"