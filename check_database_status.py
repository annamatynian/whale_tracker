"""
Check Database Configuration and Status
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env
load_dotenv()

print("\n" + "="*80)
print("📊 DATABASE CONFIGURATION STATUS")
print("="*80)

# Check database settings
db_type = os.getenv('DB_TYPE', 'sqlite')
sqlite_path = os.getenv('SQLITE_PATH', 'data/database/whale_tracker.db')
db_host = os.getenv('DB_HOST', 'localhost')
db_name = os.getenv('DB_NAME', 'whale_tracker')

print(f"\n1️⃣ Database Type: {db_type.upper()}")
print("-" * 80)

if db_type == 'sqlite':
    print(f"   SQLite Database Path: {sqlite_path}")

    # Check if database file exists
    db_path = Path(sqlite_path)
    if db_path.exists():
        size_bytes = db_path.stat().st_size
        size_kb = size_bytes / 1024
        print(f"   ✅ Database file EXISTS")
        print(f"      Size: {size_kb:.2f} KB ({size_bytes} bytes)")

        # Try to query the database
        try:
            import sqlite3
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Check tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()

            if tables:
                print(f"\n   📋 Tables in database ({len(tables)} tables):")
                for table in tables:
                    table_name = table[0]
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    print(f"      - {table_name}: {count} rows")
            else:
                print(f"\n   ⚠️  Database is empty (no tables)")
                print(f"      Run database migrations to create tables:")
                print(f"      > alembic upgrade head")

            conn.close()

        except Exception as e:
            print(f"   ❌ Error reading database: {e}")
    else:
        print(f"   ❌ Database file DOES NOT EXIST")
        print(f"      Database will be created on first run")
        print(f"      Location: {db_path.absolute()}")

        # Check if directory exists
        db_dir = db_path.parent
        if not db_dir.exists():
            print(f"\n   📁 Creating database directory...")
            db_dir.mkdir(parents=True, exist_ok=True)
            print(f"      ✅ Directory created: {db_dir.absolute()}")

elif db_type == 'postgresql':
    print(f"   PostgreSQL Host: {db_host}")
    print(f"   Database Name: {db_name}")
    print(f"\n   ⚠️  PostgreSQL configuration detected")
    print(f"      Ensure PostgreSQL server is running and accessible")

print("\n2️⃣ Detection Repository Status:")
print("-" * 80)

# Check if DetectionRepository is configured in main.py
main_py_path = Path("main.py")
if main_py_path.exists():
    with open(main_py_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if 'DetectionRepository' in content or 'detection_repo' in content:
        print("   ✅ DetectionRepository is CONFIGURED in main.py")

        if 'SQLDetectionRepository' in content:
            print("      Type: SQLDetectionRepository (will save to database)")
        elif 'InMemoryDetectionRepository' in content:
            print("      Type: InMemoryDetectionRepository (memory only, not persistent)")

        # Check if auto-save is enabled
        if 'save_detection' in content:
            print("      ✅ Auto-save detections: ENABLED")
        else:
            print("      ⚠️  Auto-save detections: Status unknown")
    else:
        print("   ⚠️  DetectionRepository NOT found in main.py")
        print("      Database storage may not be active")

print("\n3️⃣ Storage Behavior:")
print("-" * 80)
print("   When you run main.py:")
print()
if db_type == 'sqlite':
    print(f"   ✅ All whale detections will be saved to:")
    print(f"      {Path(sqlite_path).absolute()}")
    print()
    print("   📊 Data that will be stored:")
    print("      - One-hop detections (whale → intermediate → exchange)")
    print("      - Transaction metadata (amounts, timestamps, hashes)")
    print("      - Confidence scores (time, gas, nonce, amount correlations)")
    print("      - Alert status (sent/not sent)")
    print()
    print("   📈 You can query historical data:")
    print("      - View all detections: SELECT * FROM one_hop_detections")
    print("      - Count detections: SELECT COUNT(*) FROM one_hop_detections")
    print("      - Filter by confidence: WHERE total_confidence > 80")
else:
    print(f"   ✅ All whale detections will be saved to PostgreSQL:")
    print(f"      Database: {db_name} on {db_host}")

print("\n4️⃣ How to view stored data:")
print("-" * 80)
if db_type == 'sqlite':
    print("   Option 1 - SQLite command line:")
    print(f"   > sqlite3 {sqlite_path}")
    print(f"   sqlite> SELECT * FROM one_hop_detections LIMIT 10;")
    print()
    print("   Option 2 - Python script:")
    print("   > python -c \"import sqlite3; ...")
    print()
    print("   Option 3 - DB Browser for SQLite (GUI):")
    print("   Download: https://sqlitebrowser.org/")

print("\n" + "="*80)
print("✅ DATABASE CHECK COMPLETE")
print("="*80)
print()
