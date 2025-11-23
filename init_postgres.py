"""
Initialize PostgreSQL Database for Whale Tracker

This script creates all tables in PostgreSQL database using Alembic migrations.
"""
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load .env
load_dotenv()

print("\n" + "="*80)
print("🐘 INITIALIZING WHALE TRACKER DATABASE (PostgreSQL)")
print("="*80)

# Get database configuration from .env
db_type = os.getenv('DB_TYPE', 'sqlite')

if db_type.lower() != 'postgresql':
    print(f"\n⚠️  Warning: DB_TYPE is set to '{db_type}'")
    print(f"   For PostgreSQL, set DB_TYPE=postgresql in .env file")
    print(f"\n   Continue anyway with PostgreSQL? (y/n): ", end="")

    response = input().strip().lower()
    if response != 'y':
        print("\n❌ Cancelled. Please update .env file and try again.")
        sys.exit(0)

# PostgreSQL configuration
db_host = os.getenv('DB_HOST', 'localhost')
db_port = os.getenv('DB_PORT', '5432')
db_name = os.getenv('DB_NAME', 'whale_tracker')
db_user = os.getenv('DB_USER', 'postgres')
db_password = os.getenv('DB_PASSWORD', '')

print(f"\n1️⃣ Database Configuration:")
print(f"   Type: PostgreSQL")
print(f"   Host: {db_host}:{db_port}")
print(f"   Database: {db_name}")
print(f"   User: {db_user}")

# Test PostgreSQL connection
print(f"\n2️⃣ Testing PostgreSQL connection...")

try:
    from sqlalchemy import create_engine, text

    # Connection URL
    db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    # Try to connect
    engine = create_engine(db_url, echo=False)

    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        print(f"   ✅ Connected successfully!")
        print(f"   PostgreSQL version: {version.split(',')[0]}")

except Exception as e:
    print(f"\n❌ Failed to connect to PostgreSQL:")
    print(f"   Error: {e}")
    print(f"\n💡 Troubleshooting:")
    print(f"   1. Make sure PostgreSQL is running:")
    print(f"      Windows: Check Services → PostgreSQL")
    print(f"      Linux/Mac: sudo systemctl status postgresql")
    print(f"   2. Verify .env credentials:")
    print(f"      DB_HOST={db_host}")
    print(f"      DB_PORT={db_port}")
    print(f"      DB_NAME={db_name}")
    print(f"      DB_USER={db_user}")
    print(f"      DB_PASSWORD=<your_password>")
    print(f"   3. Create database if it doesn't exist:")
    print(f"      psql -U postgres -c 'CREATE DATABASE {db_name};'")
    print()
    sys.exit(1)

# Create tables
print(f"\n3️⃣ Creating database tables...")

try:
    from models.database import Base

    # Create all tables
    Base.metadata.create_all(engine)
    print(f"   ✅ Tables created successfully!")

    # List created tables
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    print(f"\n4️⃣ Created Tables ({len(tables)} total):")
    for table in tables:
        columns = inspector.get_columns(table)
        print(f"   📋 {table} ({len(columns)} columns)")

    # Count rows in each table
    print(f"\n5️⃣ Table Status:")
    with engine.connect() as conn:
        for table in tables:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.fetchone()[0]
            print(f"   📊 {table}: {count} rows")

    print(f"\n" + "="*80)
    print(f"✅ POSTGRESQL DATABASE INITIALIZATION COMPLETE")
    print(f"="*80)
    print(f"\nYou can now run main.py - all detections will be saved to PostgreSQL!")
    print(f"\n📊 To view data:")
    print(f"   psql -U {db_user} -d {db_name}")
    print(f"   SELECT * FROM one_hop_detections LIMIT 10;")
    print(f"\n🔄 To use PostgreSQL, update .env file:")
    print(f"   DB_TYPE=postgresql")
    print()

except Exception as e:
    print(f"\n❌ Error creating tables: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
