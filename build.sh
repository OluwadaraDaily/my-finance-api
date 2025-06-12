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
# Get the current head revision from migration files
echo "🔍 Getting current head revision..."
HEAD_REVISION=$(PYTHONPATH=$PYTHONPATH:$(pwd) alembic heads | head -n 1 | awk '{print $1}')
echo "📋 Current head revision: $HEAD_REVISION"

# Try to stamp normally first, if it fails, use direct database update
echo "📌 Attempting to stamp database to revision: $HEAD_REVISION"
if ! PYTHONPATH=$PYTHONPATH:$(pwd) alembic stamp $HEAD_REVISION --purge; then
    echo "⚠️  Stamp failed, attempting direct database fix..."
    
    # Create a temporary Python script to fix the alembic_version table
    cat > fix_alembic_version.py << EOF
import os
import sys
from sqlalchemy import create_engine, text

# Get database URL from environment
db_url = os.environ.get('DB_URL')
if not db_url:
    print("ERROR: DB_URL environment variable not set")
    sys.exit(1)

try:
    engine = create_engine(db_url)
    with engine.connect() as conn:
        # Update or insert the correct revision
        conn.execute(text("DELETE FROM alembic_version"))
        conn.execute(text("INSERT INTO alembic_version (version_num) VALUES (:version)"), {"version": "$HEAD_REVISION"})
        conn.commit()
        print(f"✅ Successfully updated alembic_version to {HEAD_REVISION}")
except Exception as e:
    print(f"❌ Failed to update database: {e}")
    sys.exit(1)
EOF

    # Run the fix script
    PYTHONPATH=$PYTHONPATH:$(pwd) python fix_alembic_version.py
    
    # Clean up
    rm fix_alembic_version.py
fi

# Now run migrations
echo "⬆️  Running upgrade to head..."
PYTHONPATH=$PYTHONPATH:$(pwd) alembic upgrade head

echo "✅ Build process completed!"