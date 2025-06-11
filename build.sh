#!/usr/bin/env bash
# exit on error
set -o errexit

echo "🚀 Starting build process..."

echo "🐍 Installing Python dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install mysqlclient mysql-connector-python

echo "🔄 Running database migrations..."
alembic upgrade head

echo "✅ Build process completed!"