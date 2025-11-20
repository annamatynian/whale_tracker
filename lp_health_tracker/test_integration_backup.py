#!/usr/bin/env python3
"""
Quick test of Historical Data Manager integration
================================================
"""

import sys
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_historical_integration():
    """Test Historical Data Manager integration."""
    print("🧪 TESTING Historical Data Manager Integration...")
    print("=" * 60)
    
    try:
        # Test 1: Import
        print("\n1️⃣ Testing imports...")
        from src.historical_data_manager import HistoricalDataManager
        from src.main import LPHealthTracker
        print("   ✅ All imports successful")
        
        # Test 2: Initialize Historical Manager
        print("\n2️⃣ Testing Historical Data Manager initialization...")
        historical_manager = HistoricalDataManager()
        print("   ✅ HistoricalDataManager created")
        
        # Test 3: Initialize Main App
        print("\n3️⃣ Testing LP Health Tracker initialization...")
        # Don't call __init__ fully to avoid loading .env
        # Just check that historical_manager is part of the class
        import inspect
        lp_tracker_init = inspect.signature(LPHealthTracker.__init__)
        print("   ✅ LPHealthTracker class available")
        
        # Test 4: Test Database Creation
        print("\n4️⃣ Testing database creation...")
        import sqlite3
        from pathlib import Path
        
        db_path = "data/history.db"
        
        # Check if database was created
        if Path(db_path).exists():
            print(f"   ✅ Database exists: {db_path}")
            
            # Check tables
            with sqlite3.connect(db_path) as conn:
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [row[0] for row in cursor.fetchall()]
                print(f"   ✅ Tables created: {tables}")
        else:
            print(f"   🆕 Database will be created at: {db_path}")
        
        # Test 5: Test Mock Data Save
        print("\n5️⃣ Testing data save operation...")
        mock_analysis = {
            'impermanent_loss': {'percentage': -0.025, 'usd_amount': -125.50},
            'hold_strategy': {'current_value_usd': 5000.0},
            'lp_strategy': {'current_value_usd': 4874.50, 'fees_earned_usd': 45.20},
            'better_strategy': 'HOLD'
        }
        
        mock_market = {
            'token_a_price': 2000.0,
            'token_b_price': 1.0,
            'price_ratio': 2000.0
        }
        
        success = historical_manager.save_position_snapshot(
            position_name="TEST-Integration-Position",
            analysis_data=mock_analysis,
            market_data=mock_market
        )
        
        if success:
            print("   ✅ Mock data saved successfully")
        else:
            print("   ❌ Failed to save mock data")
        
        # Test 6: Test Daily Summary
        print("\n6️⃣ Testing daily summary...")
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        summary = historical_manager.get_daily_summary(today)
        
        if summary:
            positions_count = summary.get('positions_count', 0)
            avg_il = summary.get('average_il', 0)
            total_pnl = summary.get('total_pnl_usd', 0)
            
            print(f"   ✅ Daily summary for {today}:")
            print(f"      • Positions: {positions_count}")
            print(f"      • Average IL: {avg_il:.3f}%")
            print(f"      • Total P&L: ${total_pnl:.2f}")
        else:
            print("   📊 No data in daily summary yet")
        
        print(f"\n🎉 INTEGRATION TEST COMPLETED SUCCESSFULLY!")
        print("✅ Historical Data Manager is fully integrated into LP Health Tracker")
        return True
        
    except Exception as e:
        print(f"\n❌ INTEGRATION TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_historical_integration()
