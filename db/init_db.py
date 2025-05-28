# DB seeding logic
from db.session import engine
from db.base import Base
from db.models import *  # This imports all models
from sqlalchemy import text

def init_db():
    """Drop all tables and recreate them"""
    print("Dropping all tables...")
    # First, disable foreign key checks
    with engine.connect() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        conn.commit()
    
    # Drop all tables
    Base.metadata.drop_all(bind=engine)
    
    # Re-enable foreign key checks
    with engine.connect() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))
        conn.commit()
    
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables have been recreated successfully!")

if __name__ == "__main__":
    init_db()