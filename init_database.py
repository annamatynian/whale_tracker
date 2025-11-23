"""
Initialize SQLite Database for Whale Tracker
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env
load_dotenv()

print("\n" + "="*80)
print("🗄️  INITIALIZING WHALE TRACKER DATABASE")
print("="*80)

# Get database path from .env
db_type = os.getenv('DB_TYPE', 'sqlite')
sqlite_path = os.getenv('SQLITE_PATH', 'data/database/whale_tracker.db')

if db_type != 'sqlite':
    print(f"\n❌ Error: This script only works with SQLite")
    print(f"   Current DB_TYPE: {db_type}")
    print(f"   Change DB_TYPE=sqlite in .env file")
    sys.exit(1)

print(f"\n1️⃣ Database Configuration:")
print(f"   Type: SQLite")
print(f"   Path: {sqlite_path}")

# Ensure directory exists
db_path = Path(sqlite_path)
db_path.parent.mkdir(parents=True, exist_ok=True)
print(f"   ✅ Directory: {db_path.parent.absolute()}")

# Create database with SQLAlchemy
print(f"\n2️⃣ Creating database tables...")

from sqlalchemy import create_engine
from models.database import Base

# Create sync engine for SQLite
engine = create_engine(f"sqlite:///{sqlite_path}", echo=False)

try:
    # Create all tables
    Base.metadata.create_all(engine)
    print(f"   ✅ Tables created successfully!")

    # List created tables
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    print(f"\n3️⃣ Created Tables ({len(tables)} total):")
    for table in tables:
        columns = inspector.get_columns(table)
        print(f"   📋 {table}")
        print(f"      Columns: {len(columns)}")
        for col in columns[:5]:  # Show first 5 columns
            print(f"        - {col['name']}: {col['type']}")
        if len(columns) > 5:
            print(f"        ... and {len(columns) - 5} more")

    # Check file size
    if db_path.exists():
        size_bytes = db_path.stat().st_size
        size_kb = size_bytes / 1024
        print(f"\n4️⃣ Database File:")
        print(f"   Path: {db_path.absolute()}")
        print(f"   Size: {size_kb:.2f} KB")

    print(f"\n" + "="*80)
    print(f"✅ DATABASE INITIALIZATION COMPLETE")
    print(f"="*80)
    print(f"\nYou can now run main.py - all detections will be saved to:")
    print(f"   {db_path.absolute()}")
    print(f"\n📊 To view data:")
    print(f"   sqlite3 {sqlite_path}")
    print(f"   sqlite> SELECT * FROM one_hop_detections LIMIT 10;")
    print()

except Exception as e:
    print(f"\n❌ Error creating tables: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
