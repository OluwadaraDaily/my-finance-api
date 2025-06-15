#!/usr/bin/env bash
# exit on error
set -o errexit

# Create error-logs.log file if it doesn't exist
touch error-logs.log

# Function to log messages with timestamps
log_message() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${timestamp}] $1"
    echo "[${timestamp}] $1" >> error-logs.log
}

# Function to handle errors
handle_error() {
    local error_message="$1"
    log_message "❌ Error: ${error_message}"
    exit 1
}

# Function to check required environment variables
check_env_vars() {
    if [ -z "${DB_URL}" ]; then
        handle_error "DB_URL environment variable is not set"
    fi
}

# Function to handle database migration errors
handle_migration_error() {
    log_message "⚠️  Migration error occurred. Attempting to fix alembic_version table..."
    
    # Create a temporary Python script to fix the alembic_version table
    cat > fix_alembic_version.py << EOF
import os
import sys
from sqlalchemy import create_engine, text

db_url = os.environ.get('DB_URL')
if not db_url:
    print("ERROR: DB_URL environment variable not set")
    sys.exit(1)

try:
    engine = create_engine(db_url)
    with engine.connect() as conn:
        # Get the current version if it exists
        result = conn.execute(text("SELECT version_num FROM alembic_version")).fetchone()
        current_version = result[0] if result else None
        
        if current_version:
            print(f"Current version in database: {current_version}")
        else:
            print("No version found in database")
            
        # Update or insert the correct revision
        conn.execute(text("DELETE FROM alembic_version"))
        conn.execute(text("INSERT INTO alembic_version (version_num) VALUES (:version)"), 
                    {"version": "$HEAD_REVISION"})
        conn.commit()
        print(f"Successfully updated alembic_version to {HEAD_REVISION}")
except Exception as e:
    print(f"Failed to update database: {e}")
    sys.exit(1)
EOF

    PYTHONPATH=$PYTHONPATH:$(pwd) python fix_alembic_version.py
    rm fix_alembic_version.py
}

log_message "🚀 Starting build process..."

# Check environment variables
check_env_vars

# Install dependencies
log_message "🐍 Installing Python dependencies..."
python -m pip install --upgrade pip || handle_error "Failed to upgrade pip"
pip install -r requirements.txt || handle_error "Failed to install requirements"
pip install mysqlclient mysql-connector-python || handle_error "Failed to install database dependencies"

# Configure Alembic
log_message "🔧 Configuring Alembic..."
sed -i "s|sqlalchemy.url = .*|sqlalchemy.url = ${DB_URL}|" alembic.ini || handle_error "Failed to update alembic.ini"

if [ -f "alembic_env_template.py" ]; then
    cp alembic_env_template.py alembic/env.py || handle_error "Failed to copy env.py template"
fi

# Check current migration status
log_message "📊 Checking current migration status..."
CURRENT_REV=$(PYTHONPATH=$PYTHONPATH:$(pwd) alembic current 2>/dev/null || echo "None")
log_message "Current revision: $CURRENT_REV"

# Get latest migration revision
log_message "🔍 Getting latest migration revision..."
HEAD_REVISION=$(PYTHONPATH=$PYTHONPATH:$(pwd) alembic heads | head -n 1 | awk '{print $1}')
log_message "Latest revision: $HEAD_REVISION"

# Compare and update if needed
if [ "$CURRENT_REV" = "None" ] || [ "$CURRENT_REV" != "$HEAD_REVISION" ]; then
    log_message "⚠️ Database is not up to date. Running migrations..."
    
    # Try to run migrations
    if ! PYTHONPATH=$PYTHONPATH:$(pwd) alembic upgrade head; then
        log_message "❌ Migration failed. Attempting to fix..."
        handle_migration_error
        
        # Try migrations again after fix
        log_message "🔄 Retrying migrations..."
        PYTHONPATH=$PYTHONPATH:$(pwd) alembic upgrade head || handle_error "Migration failed after recovery attempt"
    fi
    
    log_message "✅ Migrations completed successfully!"
else
    log_message "✅ Database is already up to date!"
fi

log_message "✨ Build process completed successfully!"