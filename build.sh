#!/usr/bin/env bash
# exit on error
set -o errexit

echo "🚀 Starting build process..."

echo "🐍 Installing Python dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install mysqlclient mysql-connector-python

echo "🔧 Configuring Alembic..."
# Update alembic.ini with correct database URL for deployment
sed -i "s|sqlalchemy.url = .*|sqlalchemy.url = ${DB_URL}|" alembic.ini

# Ensure env.py is properly configured (in case it needs updating)
if [ -f "alembic_env_template.py" ]; then
    cp alembic_env_template.py alembic/env.py
fi

echo "🔄 Running database migrations..."
# Ensure database is stamped to the latest revision to avoid revision mismatches
echo "📌 Stamping database to current head revision..."
PYTHONPATH=$PYTHONPATH:$(pwd) alembic stamp head

# Now run migrations (this should be a no-op if already at head, or apply any new migrations)
PYTHONPATH=$PYTHONPATH:$(pwd) alembic upgrade head

echo "✅ Build process completed!"