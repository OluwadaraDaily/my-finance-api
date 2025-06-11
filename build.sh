#!/usr/bin/env bash
# exit on error
set -o errexit

echo "🚀 Starting build process..."

# Create required apt directories and fix permissions
echo "📁 Setting up apt directories..."
mkdir -p /var/lib/apt/lists/partial
chmod 755 /var/lib/apt/lists/partial

# Update apt with verbose logging
echo "📦 Updating apt packages..."
apt-get clean
apt-get update -y -v

echo "📦 Installing system dependencies..."
apt-get install -y python3-dev default-libmysqlclient-dev build-essential pkg-config

echo "🐍 Installing Python dependencies..."
pip install -r requirements.txt

echo "🔄 Running database migrations..."
alembic upgrade head

echo "✅ Build process completed!"