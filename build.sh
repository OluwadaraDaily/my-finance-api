#!/usr/bin/env bash
# exit on error
set -o errexit

echo "🚀 Starting build process..."

echo "🐍 Installing Python dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install mysqlclient mysql-connector-python

echo "🔧 Initializing Alembic..."
# Initialize alembic if it hasn't been initialized
if [ ! -d "alembic" ]; then
    alembic init alembic
    
    # Update alembic.ini with correct settings
    sed -i "s|sqlalchemy.url = .*|sqlalchemy.url = ${DB_URL}|" alembic.ini
    
    # Replace the default env.py with our template
    cp alembic_env_template.py alembic/env.py
    
    # Create initial migration
    alembic revision --autogenerate -m "Initial migration"
fi

echo "🔄 Running database migrations..."
PYTHONPATH=$PYTHONPATH:$(pwd) alembic upgrade head

echo "✅ Build process completed!"