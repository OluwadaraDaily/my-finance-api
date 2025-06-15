#!/usr/bin/env bash
# exit on error
set -o errexit

# Function to log messages with timestamps
log_message() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${timestamp}] $1"
    echo "[${timestamp}] $1" >> build-script-logs.log
}

log_message "🚀 Starting build process..."

# Check if DB_URL is set
if [ -z "${DB_URL}" ]; then
    log_message "❌ Error: DB_URL environment variable is not set"
    exit 1
fi

# Install dependencies
log_message "🐍 Installing Python dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install mysqlclient mysql-connector-python

# Configure Alembic
log_message "🔧 Configuring Alembic..."
sed -i "s|sqlalchemy.url = .*|sqlalchemy.url = ${DB_URL}|" alembic.ini

if [ -f "alembic_env_template.py" ]; then
    cp alembic_env_template.py alembic/env.py
fi

# Ensure the color column migration is applied
log_message "🔄 Ensuring color column migration is applied..."
log_message "📌 Setting database to pre-color-column state..."
PYTHONPATH=$PYTHONPATH:$(pwd) alembic stamp 78493e2f0c86

log_message "⬆️ Applying remaining migrations..."
PYTHONPATH=$PYTHONPATH:$(pwd) alembic upgrade head

log_message "✨ Build process completed successfully!"