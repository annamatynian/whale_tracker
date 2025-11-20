#!/usr/bin/env python3
"""
Final Integration Check - Historical Data Manager
==============================================
"""

def check_integration():
    print("🎯 FINAL INTEGRATION CHECK: Historical Data Manager")
    print("=" * 60)
    
    # Check 1: File exists
    print("\n1️⃣ Checking file existence...")
    try:
        from pathlib import Path
        historical_file = Path("src/historical_data_manager.py")
        if historical_file.exists():
            print("   ✅ src/historical_data_manager.py EXISTS")
        else:
            print("   ❌ src/historical_data_manager.py MISSING")
            return False
    except Exception as e:
        print(f"   ❌ Error checking files: {e}")
        return False
    
    # Check 2: Import works
    print("\n2️⃣ Checking imports...")
    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        
        from src.historical_data_manager import HistoricalDataManager
        print("   ✅ HistoricalDataManager import SUCCESSFUL")
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        return False
    
    # Check 3: Main.py integration
    print("\n3️⃣ Checking main.py integration...")
    try:
        with open("src/main.py", "r") as f:
            main_content = f.read()
            
        checks = [
            ("import", "from src.historical_data_manager import HistoricalDataManager"),
            ("init", "self.historical_manager = HistoricalDataManager()"),
            ("save_data", "self.historical_manager.save_position_snapshot"),
            ("daily_report", "self.historical_manager.get_daily_summary")
        ]
        
        for check_name, check_text in checks:
            if check_text in main_content:
                print(f"   ✅ {check_name}: INTEGRATED")
            else:
                print(f"   ❌ {check_name}: MISSING")
                return False
                
    except Exception as e:
        print(f"   ❌ Error checking main.py: {e}")
        return False
    
    # Check 4: run.py integration
    print("\n4️⃣ Checking run.py integration...")
    try:
        with open("run.py", "r") as f:
            run_content = f.read()
            
        if "test_historical_data" in run_content:
            print("   ✅ test_historical_data function: ADDED")
        else:
            print("   ❌ test_historical_data function: MISSING")
            return False
            
    except Exception as e:
        print(f"   ❌ Error checking run.py: {e}")
        return False
    
    # Check 5: Data directory
    print("\n5️⃣ Checking data directory...")
    try:
        data_dir = Path("data")
        if data_dir.exists() and data_dir.is_dir():
            print("   ✅ data/ directory: EXISTS")
        else:
            print("   ❌ data/ directory: MISSING")
            return False
    except Exception as e:
        print(f"   ❌ Error checking data directory: {e}")
        return False
    
    print(f"\n🎉 INTEGRATION CHECK COMPLETED!")
    print("✅ Historical Data Manager FULLY INTEGRATED")
    print("\n📋 READY FOR:")
    print("   • python run.py --test-config")
    print("   • python run.py (live monitoring)")
    print("   • Automatic historical data collection")
    print("   • Daily reports with historical insights")
    
    return True

if __name__ == "__main__":
    success = check_integration()
    exit(0 if success else 1)
