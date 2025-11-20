"""
Database initialization script for Crypto Multi-Agent System
Run this to create database tables and test the connection
"""

import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.config import create_tables, get_database_info, drop_tables
from database.database_manager import DatabaseManager


def initialize_database():
    """Initialize database tables and test connection."""
    print("=" * 60)
    print("🗄️ CRYPTO MULTI-AGENT DATABASE INITIALIZATION")
    print("=" * 60)
    
    try:
        # Step 1: Get database info
        db_info = get_database_info()
        print(f"📊 Database Type: {db_info['database_type']}")
        print(f"📊 Database URL: {db_info['database_url']}")
        
        # Step 2: Create tables
        print("\n📋 Creating database tables...")
        create_tables()
        
        print(f"✅ Successfully created {db_info['tables_count']} tables:")
        for table_name in db_info['table_names']:
            print(f"   - {table_name}")
        
        # Step 3: Test DatabaseManager
        print("\n🧪 Testing DatabaseManager...")
        db_manager = DatabaseManager()
        
        # Test session creation
        session_id = db_manager.create_session(cycle_number=1)
        print(f"✅ Created test session with ID: {session_id}")
        
        # Test system overview
        overview = db_manager.get_system_overview()
        print(f"✅ System overview: {overview}")
        
        print("\n🎉 DATABASE INITIALIZATION COMPLETED SUCCESSFULLY!")
        print("🚀 Ready to start analyzing crypto tokens!")
        
    except Exception as e:
        print(f"❌ DATABASE INITIALIZATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def reset_database():
    """Reset database (drop and recreate all tables)."""
    print("\n⚠️  WARNING: This will delete ALL existing data!")
    confirm = input("Type 'RESET' to confirm: ")
    
    if confirm == 'RESET':
        try:
            print("🗑️ Dropping all tables...")
            drop_tables()
            
            print("📋 Recreating tables...")
            create_tables()
            
            print("✅ Database reset completed!")
            return True
        except Exception as e:
            print(f"❌ Reset failed: {e}")
            return False
    else:
        print("❌ Reset cancelled")
        return False


def show_status():
    """Show current database status."""
    try:
        db_manager = DatabaseManager()
        overview = db_manager.get_system_overview()
        
        print("=" * 40)
        print("📊 CURRENT DATABASE STATUS")
        print("=" * 40)
        print(f"Total tokens discovered: {overview.get('total_tokens_discovered', 0)}")
        print(f"Total analysis sessions: {overview.get('total_analysis_sessions', 0)}")
        print(f"Total token analyses: {overview.get('total_token_analyses', 0)}")
        print(f"Total alerts generated: {overview.get('total_alerts_generated', 0)}")
        
        if overview.get('latest_session_timestamp'):
            print(f"Latest session: {overview['latest_session_timestamp']}")
            print(f"Latest cycle number: {overview.get('latest_cycle_number', 0)}")
        else:
            print("No analysis sessions yet")
            
    except Exception as e:
        print(f"❌ Failed to get status: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "init":
            initialize_database()
        elif command == "reset":
            reset_database()
        elif command == "status":
            show_status()
        else:
            print("Unknown command. Available commands:")
            print("  python init_database.py init   - Initialize database")
            print("  python init_database.py reset  - Reset database (WARNING: deletes all data)")
            print("  python init_database.py status - Show database status")
    else:
        # Default: initialize
        initialize_database()
